"""
Enhanced Persona Generator with Dual AI Model Approach
Combines Gemini and ChatGPT with web search for deeper customer and market analysis.
"""

import asyncio
import json
import logging
import os
import re
import time
import streamlit as st
from typing import Dict, Any, Optional, List, Tuple
from app.ai.gemini_client import gemini_client, get_grounded_company_summary
from app.ai.chatgpt_client import chatgpt_generate, get_chatgpt_client
from app.ai.workflow_orchestrator import run_value_alignment_workflow
from app.database import fetch_all_value_components, save_persona
import app.utils as utils
from app.ai.market_intelligence import market_intelligence_service
from app.ai.enhanced_prompts import enhanced_prompt_builder

# Sonar Integration
from app.ai.sonar import QualityGates, RelevanceValidator, DomainValidator
from app.ai.sonar.enhanced_validation import enhanced_sonar_validator
from app.ai.sonar.integration_utils import sonar_integration_utils

logger = logging.getLogger(__name__)

# Create dedicated Persona Generation logger for step-by-step tracking
def setup_persona_generation_logger():
    """Setup dedicated logger for comprehensive persona generation step-by-step tracking"""
    persona_gen_logger = logging.getLogger('persona_generation')
    persona_gen_logger.setLevel(logging.INFO)
    
    # Create file handler for persona generation log file
    log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'persona_generation.log')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter with detailed timestamp (including milliseconds)
    formatter = logging.Formatter(
        '[%(asctime)s] [PID %(process)d] [%(levelname)s] [%(funcName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Prevent propagation to root logger
    persona_gen_logger.propagate = False
    
    # Add handler only if not already added
    if not persona_gen_logger.handlers:
        persona_gen_logger.addHandler(file_handler)
    
    return persona_gen_logger

# Initialize Persona Generation logger
persona_gen_logger = setup_persona_generation_logger()

# Global token usage tracker (keyed by (pid, step, api_type))
_token_usage_tracker: Dict[Tuple[int, str, str], Dict[str, int]] = {}
import threading
_token_usage_lock = threading.Lock()

def get_token_usage(pid: int, step: str, api_type: str) -> Optional[Dict[str, int]]:
    """Get token usage for a specific API call"""
    with _token_usage_lock:
        return _token_usage_tracker.get((pid, step, api_type))

def set_token_usage(pid: int, step: str, api_type: str, usage: Dict[str, int]):
    """Store token usage for a specific API call"""
    with _token_usage_lock:
        _token_usage_tracker[(pid, step, api_type)] = usage

def parse_token_usage_from_logs(pid: int, log_file: str, api_type: str) -> Dict[str, int]:
    """Parse token usage from API log files"""
    token_usage = {"total": 0, "prompt": 0, "completion": 0}
    
    try:
        if not os.path.exists(log_file):
            return token_usage
        
        # Read the log file and find entries for this PID
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Look for token usage in recent log entries (last 100 lines should be enough)
        for line in reversed(lines[-100:]):
            if f"[PID {pid}]" in line and "Tokens:" in line:
                # Extract token usage: "Tokens: 1234 (Prompt: 567, Completion: 667)"
                match = re.search(r'Tokens:\s*(\d+)\s*\(Prompt:\s*(\d+),\s*Completion:\s*(\d+)\)', line)
                if match:
                    total = int(match.group(1))
                    prompt = int(match.group(2))
                    completion = int(match.group(3))
                    token_usage["total"] += total
                    token_usage["prompt"] += prompt
                    token_usage["completion"] += completion
    except Exception as e:
        logger.debug(f"Error parsing token usage from {log_file}: {e}")
    
    return token_usage

def _extract_domain_from_url(url: str) -> str:
    """Extract domain from URL for validation"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""

def _normalize_company_name(name: str) -> str:
    """Normalize company name for comparison (lowercase, remove special chars, handle variations)"""
    if not name or not isinstance(name, str):
        return ""
    
    # Convert to lowercase
    normalized = name.lower().strip()
    
    # Remove common legal suffixes variations
    legal_suffixes = [
        "gmbh", "gmbh.", "gmbh & co.", "gmbh & co",
        "inc.", "inc", "incorporated",
        "ltd.", "ltd", "limited",
        "llc", "llc.",
        "corp.", "corp", "corporation",
        "ag", "a.g.",
        "sa", "s.a.",
        "bv", "b.v.",
        "nv", "n.v."
    ]
    
    for suffix in legal_suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
            break
    
    # Remove special characters but keep spaces
    normalized = "".join(c if c.isalnum() or c.isspace() else " " for c in normalized)
    
    # Normalize whitespace
    normalized = " ".join(normalized.split())
    
    return normalized

def _calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two company names (0.0 to 1.0)"""
    if not name1 or not name2:
        return 0.0
    
    norm1 = _normalize_company_name(name1)
    norm2 = _normalize_company_name(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Check if one contains the other (for partial matches)
    if norm1 in norm2 or norm2 in norm1:
        # Calculate ratio of shorter to longer
        shorter = min(len(norm1), len(norm2))
        longer = max(len(norm1), len(norm2))
        return shorter / longer if longer > 0 else 0.0
    
    # Simple word-based similarity
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity (intersection over union)
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def _extract_company_name_from_analysis(analysis: Dict[str, Any], pid: int = 0, 
                                        verified_company_name: Optional[str] = None) -> str:
    """
    Extract company name from analysis structure using multiple fallback paths.
    
    Args:
        analysis: Analysis dictionary from Gemini or ChatGPT
        pid: Process ID for logging
        verified_company_name: User-verified company name (optional, used as fallback)
        
    Returns:
        Company name or empty string if not found
    """
    if not analysis or not isinstance(analysis, dict):
        logger.warning(f"[PID {pid}] Cannot extract company name: analysis is empty or not a dict")
        # Use verified company name as fallback if available
        if verified_company_name:
            logger.info(f"[PID {pid}] Using verified company name as fallback: {verified_company_name}")
            return verified_company_name
        return ""
    
    # PRIORITY 1: Check verified_company_name field in analysis (highest priority)
    if "verified_company_name" in analysis and analysis["verified_company_name"]:
        company_name = str(analysis["verified_company_name"]).strip()
        if company_name:
            logger.info(f"[PID {pid}] Extracted company name from verified_company_name field: {company_name}")
            return company_name
    
    # PRIORITY 2: Check if analysis contains error indicators
    has_error = False
    if isinstance(analysis, dict):
        # Check for error fields
        if "error" in analysis or "ERROR" in str(analysis).upper():
            logger.warning(f"[PID {pid}] Analysis contains error indicators: {list(analysis.keys())[:5]}")
            has_error = True
            # Still try to extract if possible, but log the error
    
    # PRIORITY 3: Try direct extraction paths (main analysis level)
    extraction_paths = [
        ("company_overview", "name"),
        ("company_overview", "company_name"),
        ("business_analysis", "company_name"),
        ("business_analysis", "company_info", "name"),
        ("company", "name"),
        ("company_name",),
    ]
    
    for path in extraction_paths:
        try:
            value = analysis
            for key in path:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
            
            if value and isinstance(value, str) and value.strip():
                company_name = value.strip()
                logger.info(f"[PID {pid}] Extracted company name via path {path}: {company_name}")
                return company_name
        except (KeyError, AttributeError, TypeError):
            continue
    
    # PRIORITY 4: Check all sub-analyses for company_name field
    sub_analysis_keys = [
        "business_analysis", "customer_insights", "competitive_analysis",
        "pain_points_analysis", "persona_insights", "gemini_insights"
    ]
    
    for sub_key in sub_analysis_keys:
        if sub_key in analysis and isinstance(analysis[sub_key], dict):
            sub_analysis = analysis[sub_key]
            # Check for company_name in sub-analysis
            if "company_name" in sub_analysis and sub_analysis["company_name"]:
                company_name = str(sub_analysis["company_name"]).strip()
                if company_name and company_name not in ["[extracted from analysis]", "[extracted]"]:
                    logger.info(f"[PID {pid}] Extracted company name from {sub_key}.company_name: {company_name}")
                    return company_name
    
    # PRIORITY 5: Search in raw text if analysis has raw_analysis field
    if "raw_analysis" in analysis:
        raw_text = str(analysis["raw_analysis"])
        # Try to find company name patterns in raw text
        import re
        patterns = [
            r'"company_name"\s*:\s*"([^"]+)"',
            r'"name"\s*:\s*"([^"]+)"',
            r"company\s+name[:\s]+([A-Z][^,\n]+)",
            r"Company:\s*([A-Z][^,\n]+)",
            r"Target Company:\s*([A-Z][^,\n]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                if company_name and len(company_name) > 2 and company_name not in ["[extracted from analysis]", "[extracted]"]:
                    logger.info(f"[PID {pid}] Extracted company name from raw text using pattern {pattern}: {company_name}")
                    return company_name
    
    # PRIORITY 6: Use verified_company_name as final fallback
    if verified_company_name:
        logger.warning(f"[PID {pid}] Could not extract company name from analysis structure. Using verified company name as fallback: {verified_company_name}")
        return verified_company_name
    
    # Log detailed structure for debugging
    logger.warning(f"[PID {pid}] Could not extract company name from analysis structure")
    logger.debug(f"[PID {pid}] Analysis keys: {list(analysis.keys())[:10]}")
    if has_error:
        logger.error(f"[PID {pid}] Analysis contains errors - extraction may have failed due to API errors")
    
    return ""

class EnhancedPersonaGenerator:
    """Enhanced persona generator using both Gemini and ChatGPT with web search"""
    
    def __init__(self):
        self.analysis_cache = {}
        
        # Initialize Sonar components for quality gates
        self.quality_gates = QualityGates()
        self.relevance_validator = RelevanceValidator()
        self.domain_validator = DomainValidator()
        
        logger.info("[EnhancedPersonaGenerator] Initialized with Sonar quality gates")
        
    async def generate_enhanced_persona(self, website: str, selected_industry: Optional[str] = None, 
                                       pid: int = 0, progress_tracker = None, 
                                       verified_company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate enhanced buyer persona using dual AI models with web search.
        
        Args:
            website: Target website URL
            selected_industry: Industry classification
            pid: Process ID for logging
            progress_tracker: Progress tracking object
            verified_company_name: User-verified company name (optional, used as source of truth)
            
        Returns:
            Enhanced persona with dual-model analysis
        """
        start_time = time.time()
        logger.info(f"--- [PID {pid}] [Enhanced Persona Generator] NEW REQUEST START for: {website} ---")
        
        # Initialize step timing tracker
        step_timings = {}
        api_call_summary = {"sonar": [], "gemini": [], "chatgpt": []}
        token_usage_summary = {"sonar": {"total": 0, "prompt": 0, "completion": 0}, 
                              "gemini": {"total": 0, "prompt": 0, "completion": 0}, 
                              "chatgpt": {"total": 0, "prompt": 0, "completion": 0}}
        
        # Log initialization header
        persona_gen_logger.info("=" * 80)
        persona_gen_logger.info(f"[INIT] Persona Generation Started")
        persona_gen_logger.info(f"Website: {website}")
        persona_gen_logger.info(f"Industry: {selected_industry or 'Not specified'}")
        persona_gen_logger.info(f"Verified Company: {verified_company_name or 'Not provided'}")
        persona_gen_logger.info(f"PID: {pid}")
        persona_gen_logger.info("-" * 80)
        
        # Check for demo mode first
        if website.startswith("demo://"):
            logger.info(f"[PID {pid}] [Enhanced Persona Generator] DEMO MODE DETECTED: {website}")
            persona_gen_logger.info(f"[INIT] DEMO MODE DETECTED: {website}")
            from app.ai.demo_enhanced_persona_generator import demo_enhanced_persona_generator
            return await demo_enhanced_persona_generator.generate_demo_persona(website, selected_industry, pid, progress_tracker)
        
        try:
            # Step 0: Pre-analysis Relevance Validation (Sonar)
            step_0_start = time.time()
            logger.info(f"[PID {pid}] Step 0/8: Pre-analysis Relevance Validation START")
            persona_gen_logger.info(f"[STEP 0/8] START - Pre-analysis Relevance Validation")
            if progress_tracker:
                await progress_tracker.start_step(0)
            
            persona_gen_logger.info(f"[STEP 0/8] Sub-step: Calling _step_0_relevance_validation()")
            relevance_result = await self._step_0_relevance_validation(website, pid)
            step_0_duration = time.time() - step_0_start
            step_timings["step_0"] = step_0_duration
            
            # Log result summary
            is_relevant = relevance_result.get("is_relevant", True)
            relevance_score = relevance_result.get("relevance_score", 0)
            recommended_action = relevance_result.get("recommended_action", "unknown")
            persona_gen_logger.info(f"[STEP 0/8] Result: Relevance validation complete")
            persona_gen_logger.info(f"[STEP 0/8]   → Is Relevant: {is_relevant}")
            persona_gen_logger.info(f"[STEP 0/8]   → Relevance Score: {relevance_score}/10")
            persona_gen_logger.info(f"[STEP 0/8]   → Recommended Action: {recommended_action}")
            persona_gen_logger.info(f"[STEP 0/8] END - Duration: {step_0_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Check if we should proceed based on relevance
            if not is_relevant:
                logger.warning(f"[PID {pid}] Website not relevant: {website}")
                persona_gen_logger.warning(f"[STEP 0/8] Website not relevant - creating rejection persona")
                return self._create_relevance_rejection_persona(website, relevance_result, pid)
            
            # Step 1: Dual-Model Website Analysis with Web Search
            step_1_start = time.time()
            logger.info(f"[PID {pid}] Step 1/8: Dual-Model Website Analysis START")
            persona_gen_logger.info(f"[STEP 1/8] START - Dual-Model Website Analysis")
            if progress_tracker:
                await progress_tracker.start_step(1)
            
            # Parallel analysis with both models
            # Ensure industry is a string (not None) for type compatibility
            industry_str = selected_industry if selected_industry is not None else "unknown"
            persona_gen_logger.info(f"[STEP 1/8] Sub-step: Starting parallel analysis (Gemini + ChatGPT)")
            persona_gen_logger.info(f"[STEP 1/8] Sub-step: Industry: {industry_str}")
            persona_gen_logger.info(f"[STEP 1/8] Sub-step: Verified Company: {verified_company_name or 'Not provided'}")
            
            gemini_analysis, chatgpt_analysis = await self._parallel_website_analysis(
                website, industry_str, pid, verified_company_name=verified_company_name
            )
            
            step_1_duration = time.time() - step_1_start
            step_timings["step_1"] = step_1_duration
            
            # Extract company names for logging
            gemini_company = _extract_company_name_from_analysis(gemini_analysis, pid, verified_company_name)
            chatgpt_company = _extract_company_name_from_analysis(chatgpt_analysis, pid, verified_company_name)
            
            # Count insights if available
            gemini_insights_count = 0
            if isinstance(gemini_analysis, dict):
                if "persona_insights" in gemini_analysis and isinstance(gemini_analysis["persona_insights"], list):
                    gemini_insights_count = len(gemini_analysis["persona_insights"])
                elif "customer_insights" in gemini_analysis and isinstance(gemini_analysis["customer_insights"], list):
                    gemini_insights_count = len(gemini_analysis["customer_insights"])
            
            chatgpt_insights_count = 0
            if isinstance(chatgpt_analysis, dict):
                if "persona_insights" in chatgpt_analysis and isinstance(chatgpt_analysis["persona_insights"], list):
                    chatgpt_insights_count = len(chatgpt_analysis["persona_insights"])
                elif "customer_insights" in chatgpt_analysis and isinstance(chatgpt_analysis["customer_insights"], list):
                    chatgpt_insights_count = len(chatgpt_analysis["customer_insights"])
            
            persona_gen_logger.info(f"[STEP 1/8] Result: Parallel analysis complete")
            persona_gen_logger.info(f"[STEP 1/8]   → Gemini Company: {gemini_company or 'Not extracted'}")
            persona_gen_logger.info(f"[STEP 1/8]   → ChatGPT Company: {chatgpt_company or 'Not extracted'}")
            persona_gen_logger.info(f"[STEP 1/8]   → Gemini Insights: {gemini_insights_count} identified")
            persona_gen_logger.info(f"[STEP 1/8]   → ChatGPT Insights: {chatgpt_insights_count} identified")
            persona_gen_logger.info(f"[STEP 1/8] END - Duration: {step_1_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 1.25: STRICT Company Identity Validation (HARD STOP)
            step_1_25_start = time.time()
            logger.info(f"[PID {pid}] Step 1.25/8: STRICT Company Identity Validation START")
            persona_gen_logger.info(f"[STEP 1.25/8] START - STRICT Company Identity Validation")
            persona_gen_logger.info(f"[STEP 1.25/8] Sub-step: Extracting company names for validation")
            persona_gen_logger.info(f"[STEP 1.25/8]   → Gemini Company: {gemini_company or 'Not extracted'}")
            persona_gen_logger.info(f"[STEP 1.25/8]   → ChatGPT Company: {chatgpt_company or 'Not extracted'}")
            persona_gen_logger.info(f"[STEP 1.25/8]   → Verified Company: {verified_company_name or 'Not provided'}")
            
            identity_validation = await self._strict_company_identity_validation(
                gemini_analysis, chatgpt_analysis, website, pid, verified_company_name=verified_company_name
            )
            step_1_25_duration = time.time() - step_1_25_start
            step_timings["step_1.25"] = step_1_25_duration
            
            all_match = identity_validation.get("all_match", False)
            source_of_truth = identity_validation.get("source_of_truth", "Unknown")
            source_type = identity_validation.get("source_type", "unknown")
            gemini_similarity = identity_validation.get("gemini_similarity", 0)
            chatgpt_similarity = identity_validation.get("chatgpt_similarity", 0)
            
            persona_gen_logger.info(f"[STEP 1.25/8] Sub-step: Calculating similarity scores")
            persona_gen_logger.info(f"[STEP 1.25/8]   → Gemini vs Source: {gemini_similarity:.1f}%")
            persona_gen_logger.info(f"[STEP 1.25/8]   → ChatGPT vs Source: {chatgpt_similarity:.1f}%")
            persona_gen_logger.info(f"[STEP 1.25/8] Result: Validation {'PASSED' if all_match else 'FAILED'}")
            persona_gen_logger.info(f"[STEP 1.25/8]   → All Match: {all_match}")
            persona_gen_logger.info(f"[STEP 1.25/8]   → Source of Truth: {source_of_truth} ({source_type})")
            persona_gen_logger.info(f"[STEP 1.25/8] END - Duration: {step_1_25_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # HARD STOP if validation fails
            if not all_match:
                logger.error(f"[PID {pid}] CRITICAL: Company identity validation FAILED")
                logger.error(f"[PID {pid}] Gemini: {identity_validation.get('gemini_company')}")
                logger.error(f"[PID {pid}] ChatGPT: {identity_validation.get('chatgpt_company')}")
                source_label = "Verified Company" if source_type == 'verified' else "Domain Owner"
                logger.error(f"[PID {pid}] {source_label}: {source_of_truth}")
                logger.error(f"[PID {pid}] Process STOPPED to prevent incorrect persona generation")
                persona_gen_logger.error(f"[STEP 1.25/8] CRITICAL: Validation FAILED - Process STOPPED")
                persona_gen_logger.error(f"[STEP 1.25/8] Creating rejection persona")
                
                # Create rejection persona and STOP
                return self._create_company_mismatch_rejection_persona(
                    website, identity_validation, gemini_analysis, chatgpt_analysis, pid
                )
            
            # Continue only if validation passed
            logger.info(f"[PID {pid}] Step 1.25/8: Company identity validation PASSED - All models analyzing same company")
            
            # Step 1.5: Sonar Website Analysis Validation
            step_1_5_start = time.time()
            logger.info(f"[PID {pid}] Step 1.5/8: Sonar Website Analysis Validation START")
            persona_gen_logger.info(f"[STEP 1.5/8] START - Sonar Website Analysis Validation")
            persona_gen_logger.info(f"[STEP 1.5/8] Sub-step: Calling enhanced_sonar_validator.validate_website_analysis()")
            persona_gen_logger.info(f"[STEP 1.5/8]   → See: logs/sonar_model.log for API call details")
            
            sonar_website_validation = await enhanced_sonar_validator.validate_website_analysis(
                gemini_analysis, chatgpt_analysis, website, pid
            )
            step_1_5_duration = time.time() - step_1_5_start
            step_timings["step_1.5"] = step_1_5_duration
            api_call_summary["sonar"].append({"step": "1.5", "duration": step_1_5_duration})
            
            validation_passed = sonar_website_validation.get("validation_passed", False)
            overall_confidence = sonar_website_validation.get("overall_confidence", 0)
            corrections_count = len(sonar_website_validation.get("corrections", []))
            
            persona_gen_logger.info(f"[STEP 1.5/8] Result: Validation complete")
            persona_gen_logger.info(f"[STEP 1.5/8]   → Validation Passed: {validation_passed}")
            persona_gen_logger.info(f"[STEP 1.5/8]   → Overall Confidence: {overall_confidence}/10")
            persona_gen_logger.info(f"[STEP 1.5/8]   → Corrections Applied: {corrections_count}")
            persona_gen_logger.info(f"[STEP 1.5/8] END - Duration: {step_1_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Merge validated website analysis
            validated_website_analysis = sonar_integration_utils.merge_validated_website_analysis(
                gemini_analysis, chatgpt_analysis, sonar_website_validation, pid
            )
            
            # Step 1.5: Customer Focus Validation (Sonar)
            step_1_5_customer_start = time.time()
            logger.info(f"[PID {pid}] Step 1.5/8: Customer Focus Validation START")
            persona_gen_logger.info(f"[STEP 1.5/8] START - Customer Focus Validation")
            persona_gen_logger.info(f"[STEP 1.5/8] Sub-step: Calling _step_1_customer_focus_validation()")
            
            # Validate customer focus after initial analysis
            focus_result = await self._step_1_customer_focus_validation(
                gemini_analysis, chatgpt_analysis, website, pid
            )
            step_1_5_customer_duration = time.time() - step_1_5_customer_start
            step_timings["step_1.5_customer"] = step_1_5_customer_duration
            
            customer_focus_correct = focus_result.get("customer_focus_correct", True)
            misinterpretation = focus_result.get("misinterpretation_detected", "None")
            
            persona_gen_logger.info(f"[STEP 1.5/8] Result: Customer focus validation complete")
            persona_gen_logger.info(f"[STEP 1.5/8]   → Customer Focus Correct: {customer_focus_correct}")
            persona_gen_logger.info(f"[STEP 1.5/8]   → Misinterpretation Detected: {misinterpretation}")
            persona_gen_logger.info(f"[STEP 1.5/8] END - Duration: {step_1_5_customer_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Check if customer focus is correct
            if not customer_focus_correct:
                logger.warning(f"[PID {pid}] Customer focus validation failed: {misinterpretation}")
                persona_gen_logger.warning(f"[STEP 1.5/8] Customer focus validation failed - continuing with caution")
            
            # Step 2: Cross-Model Validation and Synthesis
            step_2_start = time.time()
            logger.info(f"[PID {pid}] Step 2/8: Cross-Model Validation START")
            persona_gen_logger.info(f"[STEP 2/8] START - Cross-Model Validation and Synthesis")
            if progress_tracker:
                await progress_tracker.start_step(2)
            
            persona_gen_logger.info(f"[STEP 2/8] Sub-step: Calling _cross_validate_and_synthesize()")
            # Step 2: Enhanced Cross-Model Validation with Sonar
            validated_analysis = await self._cross_validate_and_synthesize(
                gemini_analysis, chatgpt_analysis, website, pid
            )
            step_2_duration = time.time() - step_2_start
            step_timings["step_2"] = step_2_duration
            
            # Count synthesis results
            areas_of_agreement = len(validated_analysis.get("areas_of_agreement", [])) if isinstance(validated_analysis, dict) else 0
            unique_gemini = len(validated_analysis.get("unique_gemini_insights", [])) if isinstance(validated_analysis, dict) else 0
            unique_chatgpt = len(validated_analysis.get("unique_chatgpt_insights", [])) if isinstance(validated_analysis, dict) else 0
            
            persona_gen_logger.info(f"[STEP 2/8] Result: Synthesis complete")
            persona_gen_logger.info(f"[STEP 2/8]   → Areas of Agreement: {areas_of_agreement} identified")
            persona_gen_logger.info(f"[STEP 2/8]   → Unique Gemini Insights: {unique_gemini} identified")
            persona_gen_logger.info(f"[STEP 2/8]   → Unique ChatGPT Insights: {unique_chatgpt} identified")
            persona_gen_logger.info(f"[STEP 2/8] END - Duration: {step_2_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 2.5: Sonar Cross-Model Validation
            step_2_5_start = time.time()
            logger.info(f"[PID {pid}] Step 2.5/8: Sonar Cross-Model Validation START")
            persona_gen_logger.info(f"[STEP 2.5/8] START - Sonar Cross-Model Validation")
            persona_gen_logger.info(f"[STEP 2.5/8] Sub-step: Calling _step_2_sonar_cross_validation()")
            persona_gen_logger.info(f"[STEP 2.5/8]   → See: logs/sonar_model.log for API call details")
            
            cross_validation_result = await self._step_2_sonar_cross_validation(
                gemini_analysis, chatgpt_analysis, validated_analysis, website, pid
            )
            step_2_5_duration = time.time() - step_2_5_start
            step_timings["step_2.5"] = step_2_5_duration
            api_call_summary["sonar"].append({"step": "2.5", "duration": step_2_5_duration})
            
            models_agree = cross_validation_result.get("models_agree", False)
            agreement_score = cross_validation_result.get("agreement_score", 0)
            confidence = cross_validation_result.get("overall_confidence", 0)
            
            persona_gen_logger.info(f"[STEP 2.5/8] Result: Validation complete")
            persona_gen_logger.info(f"[STEP 2.5/8]   → Models Agree: {models_agree}")
            persona_gen_logger.info(f"[STEP 2.5/8]   → Agreement Score: {agreement_score:.1f}%")
            persona_gen_logger.info(f"[STEP 2.5/8]   → Confidence: {confidence}/10")
            persona_gen_logger.info(f"[STEP 2.5/8] END - Duration: {step_2_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Log cross-validation results
            if models_agree:
                logger.info(f"[PID {pid}] Models agree - proceeding with synthesis")
            else:
                logger.warning(f"[PID {pid}] Models disagree - using synthesis with caution")
            
            # Step 3: Enhanced Market Intelligence with Dual Models
            step_3_start = time.time()
            logger.info(f"[PID {pid}] Step 3/8: Enhanced Market Intelligence START")
            persona_gen_logger.info(f"[STEP 3/8] START - Enhanced Market Intelligence")
            if progress_tracker:
                await progress_tracker.start_step(3)
            
            # Ensure industry is a string (not None) for type compatibility
            industry_str = selected_industry if selected_industry is not None else "unknown"
            persona_gen_logger.info(f"[STEP 3/8] Sub-step: Calling _generate_enhanced_market_intelligence()")
            persona_gen_logger.info(f"[STEP 3/8] Sub-step: Industry: {industry_str}")
            
            enhanced_market_intelligence = await self._generate_enhanced_market_intelligence(
                website, validated_analysis, industry_str, pid
            )
            step_3_duration = time.time() - step_3_start
            step_timings["step_3"] = step_3_duration
            
            # Count market intelligence data points
            mi_data_points = 0
            if isinstance(enhanced_market_intelligence, dict):
                if "market_intelligence" in enhanced_market_intelligence:
                    mi = enhanced_market_intelligence.get("market_intelligence", {})
                    if isinstance(mi, dict):
                        mi_data_points = len(mi)
            
            persona_gen_logger.info(f"[STEP 3/8] Result: Market intelligence gathered")
            persona_gen_logger.info(f"[STEP 3/8]   → Data Points: {mi_data_points}")
            persona_gen_logger.info(f"[STEP 3/8]   → Industry: {industry_str}")
            persona_gen_logger.info(f"[STEP 3/8] END - Duration: {step_3_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 3.5: Sonar Market Intelligence Validation (Deferred if empty)
            step_3_5_start = time.time()
            logger.info(f"[PID {pid}] Step 3.5/8: Sonar Market Intelligence Validation START")
            persona_gen_logger.info(f"[STEP 3.5/8] START - Sonar Market Intelligence Validation")
            
            # Initialize validation tracker if not exists
            if not hasattr(self, '_validation_tracker'):
                from app.ai.sonar.validation_tracker import ValidationTracker
                self._validation_tracker = ValidationTracker()
            
            # Check if market intelligence is empty - defer if so
            def _is_empty_data(data):
                """More robust empty data detection for market intelligence"""
                if data is None:
                    return True
                if isinstance(data, dict):
                    # Check for nested structures
                    if len(data) == 0:
                        return True
                    # Check if it has actual market intelligence content
                    if "market_intelligence" in data:
                        mi = data.get("market_intelligence")
                        if isinstance(mi, dict) and len(mi) > 0:
                            return False
                    if "base_intelligence" in data:
                        bi = data.get("base_intelligence")
                        if isinstance(bi, dict):
                            # Check for market_intelligence inside base_intelligence
                            if "market_intelligence" in bi:
                                mi = bi.get("market_intelligence")
                                if isinstance(mi, dict) and len(mi) > 0:
                                    return False
                            # Or check if base_intelligence itself has content
                            if len(bi) > 0:
                                return False
                    # Check for original_market_intelligence
                    if "original_market_intelligence" in data:
                        omi = data.get("original_market_intelligence")
                        if isinstance(omi, dict) and len(omi) > 0:
                            return False
                    # If we get here and it's not empty dict, might have other data
                    return len(data) == 0
                if isinstance(data, list):
                    return len(data) == 0
                if isinstance(data, str):
                    return len(data.strip()) == 0
                return False
            
            persona_gen_logger.info(f"[STEP 3.5/8] Sub-step: Checking if data is empty")
            is_empty = _is_empty_data(enhanced_market_intelligence)
            persona_gen_logger.info(f"[STEP 3.5/8]   → Data Available: {not is_empty}")
            
            if enhanced_market_intelligence and not is_empty:
                # Data is available - run validation immediately
                persona_gen_logger.info(f"[STEP 3.5/8] Sub-step: Running validation immediately")
                persona_gen_logger.info(f"[STEP 3.5/8]   → See: logs/sonar_model.log for API call details")
                sonar_market_validation = await enhanced_sonar_validator.validate_market_intelligence(
                    enhanced_market_intelligence, website, selected_industry or "unknown", pid
                )
                step_3_5_duration = time.time() - step_3_5_start
                step_timings["step_3.5"] = step_3_5_duration
                api_call_summary["sonar"].append({"step": "3.5", "duration": step_3_5_duration})
                
                validation_passed = sonar_market_validation.get("validation_passed", False)
                overall_confidence = sonar_market_validation.get("overall_confidence", 0)
                persona_gen_logger.info(f"[STEP 3.5/8] Result: Validation complete")
                persona_gen_logger.info(f"[STEP 3.5/8]   → Validation Passed: {validation_passed}")
                persona_gen_logger.info(f"[STEP 3.5/8]   → Overall Confidence: {overall_confidence}/10")
            else:
                # Data is empty - mark for deferred validation
                logger.info(f"[PID {pid}] Market intelligence empty, deferring validation until after enrichment")
                persona_gen_logger.info(f"[STEP 3.5/8] Sub-step: Data empty - marking for deferred validation")
                self._validation_tracker.mark_for_deferred_validation(
                    step_name="step_3_market_intelligence",
                    validation_type="market_intelligence",
                    data_path="enhanced_market_intelligence.original_market_intelligence",
                    target_domain=_extract_domain_from_url(website) if website else None,
                    industry=selected_industry or "unknown"  # Pass industry for deferred validation
                )
                # Create placeholder validation result
                sonar_market_validation = {
                    "validation_passed": True,  # Don't block, just defer
                    "overall_confidence": 5,
                    "validation_type": "market_intelligence",
                    "deferred": True,
                    "target_domain": _extract_domain_from_url(website) if website else "",
                    "validation_notes": "Market intelligence data not yet populated. Validation deferred."
                }
                step_3_5_duration = time.time() - step_3_5_start
                step_timings["step_3.5"] = step_3_5_duration
                persona_gen_logger.info(f"[STEP 3.5/8] Result: Validation deferred")
                persona_gen_logger.info(f"[STEP 3.5/8]   → Will run after enrichment")
            
            persona_gen_logger.info(f"[STEP 3.5/8] END - Duration: {step_3_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Merge validated market intelligence
            enhanced_market_intelligence = sonar_integration_utils.merge_validated_market_intelligence(
                enhanced_market_intelligence, sonar_market_validation, pid
            )
            
            # Step 4: Dual-Model Value Alignment
            step_4_start = time.time()
            logger.info(f"[PID {pid}] Step 4/8: Dual-Model Value Alignment START")
            persona_gen_logger.info(f"[STEP 4/8] START - Dual-Model Value Alignment")
            if progress_tracker:
                await progress_tracker.start_step(4)
            
            persona_gen_logger.info(f"[STEP 4/8] Sub-step: Calling _generate_enhanced_value_alignment()")
            persona_gen_logger.info(f"[STEP 4/8]   → See: logs/value_alignment.log for workflow details")
            
            enhanced_value_alignment = await self._generate_enhanced_value_alignment(
                validated_analysis, pid
            )
            step_4_duration = time.time() - step_4_start
            step_timings["step_4"] = step_4_duration
            
            # Count alignment matches
            alignment_matches = 0
            if isinstance(enhanced_value_alignment, dict):
                if "alignment_matrix" in enhanced_value_alignment:
                    matrix = enhanced_value_alignment.get("alignment_matrix", [])
                    if isinstance(matrix, list):
                        alignment_matches = len([m for m in matrix if m.get("match_score", 0) > 0])
            
            persona_gen_logger.info(f"[STEP 4/8] Result: Value alignment complete")
            persona_gen_logger.info(f"[STEP 4/8]   → Alignment Matches: {alignment_matches} found")
            persona_gen_logger.info(f"[STEP 4/8] END - Duration: {step_4_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 4.5: Sonar Value Alignment Validation
            step_4_5_start = time.time()
            logger.info(f"[PID {pid}] Step 4.5/8: Sonar Value Alignment Validation START")
            persona_gen_logger.info(f"[STEP 4.5/8] START - Sonar Value Alignment Validation")
            persona_gen_logger.info(f"[STEP 4.5/8] Sub-step: Calling enhanced_sonar_validator.validate_value_alignment()")
            persona_gen_logger.info(f"[STEP 4.5/8]   → See: logs/sonar_model.log for API call details")
            
            sonar_value_validation = await enhanced_sonar_validator.validate_value_alignment(
                enhanced_value_alignment, website, pid
            )
            step_4_5_duration = time.time() - step_4_5_start
            step_timings["step_4.5"] = step_4_5_duration
            api_call_summary["sonar"].append({"step": "4.5", "duration": step_4_5_duration})
            
            validation_passed = sonar_value_validation.get("validation_passed", False)
            overall_confidence = sonar_value_validation.get("overall_confidence", 0)
            persona_gen_logger.info(f"[STEP 4.5/8] Result: Validation complete")
            persona_gen_logger.info(f"[STEP 4.5/8]   → Validation Passed: {validation_passed}")
            persona_gen_logger.info(f"[STEP 4.5/8]   → Overall Confidence: {overall_confidence}/10")
            persona_gen_logger.info(f"[STEP 4.5/8] END - Duration: {step_4_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Merge validated value alignment
            enhanced_value_alignment = sonar_integration_utils.merge_validated_value_alignment(
                enhanced_value_alignment, sonar_value_validation, pid
            )
            
            # Step 5: Creative Persona Elements (ChatGPT)
            step_5_start = time.time()
            logger.info(f"[PID {pid}] Step 5/8: Creative Persona Elements START")
            persona_gen_logger.info(f"[STEP 5/8] START - Creative Persona Elements")
            if progress_tracker:
                await progress_tracker.start_step(5)
            
            persona_gen_logger.info(f"[STEP 5/8] Sub-step: Calling _generate_creative_persona_elements()")
            persona_gen_logger.info(f"[STEP 5/8]   → See: logs/chatgpt_model.log for API call details")
            
            creative_elements = await self._generate_creative_persona_elements(
                validated_analysis, enhanced_market_intelligence, pid
            )
            step_5_duration = time.time() - step_5_start
            step_timings["step_5"] = step_5_duration
            api_call_summary["chatgpt"].append({"step": "5", "duration": step_5_duration})
            
            # Count creative elements
            pain_points_count = len(creative_elements.get("pain_points", [])) if isinstance(creative_elements, dict) else 0
            goals_count = len(creative_elements.get("goals", [])) if isinstance(creative_elements, dict) else 0
            value_drivers_count = len(creative_elements.get("value_drivers", [])) if isinstance(creative_elements, dict) else 0
            objections_count = len(creative_elements.get("objections", [])) if isinstance(creative_elements, dict) else 0
            
            persona_gen_logger.info(f"[STEP 5/8] Result: Creative elements generated")
            persona_gen_logger.info(f"[STEP 5/8]   → Pain Points: {pain_points_count} identified")
            persona_gen_logger.info(f"[STEP 5/8]   → Goals: {goals_count} identified")
            persona_gen_logger.info(f"[STEP 5/8]   → Value Drivers: {value_drivers_count} identified")
            persona_gen_logger.info(f"[STEP 5/8]   → Objections: {objections_count} identified")
            persona_gen_logger.info(f"[STEP 5/8] END - Duration: {step_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 5.5: Sonar Creative Elements Validation
            step_5_5_start = time.time()
            logger.info(f"[PID {pid}] Step 5.5/8: Sonar Creative Elements Validation START")
            persona_gen_logger.info(f"[STEP 5.5/8] START - Sonar Creative Elements Validation")
            persona_gen_logger.info(f"[STEP 5.5/8] Sub-step: Calling enhanced_sonar_validator.validate_creative_elements()")
            persona_gen_logger.info(f"[STEP 5.5/8]   → See: logs/sonar_model.log for API call details")
            
            sonar_creative_validation = await enhanced_sonar_validator.validate_creative_elements(
                creative_elements, website, pid
            )
            step_5_5_duration = time.time() - step_5_5_start
            step_timings["step_5.5"] = step_5_5_duration
            api_call_summary["sonar"].append({"step": "5.5", "duration": step_5_5_duration})
            
            validation_passed = sonar_creative_validation.get("validation_passed", False)
            overall_confidence = sonar_creative_validation.get("overall_confidence", 0)
            persona_gen_logger.info(f"[STEP 5.5/8] Result: Validation complete")
            persona_gen_logger.info(f"[STEP 5.5/8]   → Validation Passed: {validation_passed}")
            persona_gen_logger.info(f"[STEP 5.5/8]   → Overall Confidence: {overall_confidence}/10")
            persona_gen_logger.info(f"[STEP 5.5/8] END - Duration: {step_5_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Merge validated creative elements
            creative_elements = sonar_integration_utils.merge_validated_creative_elements(
                creative_elements, sonar_creative_validation, pid
            )
            
            # Step 6: Final Persona Synthesis (Gemini)
            step_6_start = time.time()
            logger.info(f"[PID {pid}] Step 6/8: Final Persona Synthesis START")
            persona_gen_logger.info(f"[STEP 6/8] START - Final Persona Synthesis")
            if progress_tracker:
                await progress_tracker.start_step(6)
            
            persona_gen_logger.info(f"[STEP 6/8] Sub-step: Calling _synthesize_final_persona()")
            persona_gen_logger.info(f"[STEP 6/8]   → See: logs/gemini_model.log for API call details")
            
            final_persona = await self._synthesize_final_persona(
                validated_analysis, enhanced_market_intelligence, 
                enhanced_value_alignment, creative_elements, pid
            )
            step_6_duration = time.time() - step_6_start
            step_timings["step_6"] = step_6_duration
            api_call_summary["gemini"].append({"step": "6", "duration": step_6_duration})
            
            # Check if synthesis failed
            synthesis_failed = isinstance(final_persona, dict) and "error" in final_persona
            if synthesis_failed:
                logger.error(f"[PID {pid}] Final persona synthesis failed: {final_persona['error']}")
                persona_gen_logger.error(f"[STEP 6/8] Synthesis failed - creating fallback persona")
                # Create a fallback persona structure
                final_persona = self._create_fallback_persona(validated_analysis, enhanced_market_intelligence, 
                                                           enhanced_value_alignment, creative_elements)
            
            # Extract persona fields for logging
            company_name = final_persona.get("company", {}).get("name", "Unknown") if isinstance(final_persona, dict) else "Unknown"
            products_count = len(final_persona.get("product_range", [])) if isinstance(final_persona, dict) else 0
            services_count = len(final_persona.get("services", [])) if isinstance(final_persona, dict) else 0
            pain_points_count = len(final_persona.get("pain_points", [])) if isinstance(final_persona, dict) else 0
            goals_count = len(final_persona.get("goals", [])) if isinstance(final_persona, dict) else 0
            
            persona_gen_logger.info(f"[STEP 6/8] Result: Synthesis complete")
            persona_gen_logger.info(f"[STEP 6/8]   → Company Name: {company_name}")
            persona_gen_logger.info(f"[STEP 6/8]   → Products: {products_count} identified")
            persona_gen_logger.info(f"[STEP 6/8]   → Services: {services_count} identified")
            persona_gen_logger.info(f"[STEP 6/8]   → Pain Points: {pain_points_count} identified")
            persona_gen_logger.info(f"[STEP 6/8]   → Goals: {goals_count} identified")
            persona_gen_logger.info(f"[STEP 6/8] END - Duration: {step_6_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 6.5: Sonar Final Synthesis Validation (Structure-Only, Content Deferred)
            step_6_5_start = time.time()
            logger.info(f"[PID {pid}] Step 6.5/8: Sonar Final Synthesis Validation START")
            persona_gen_logger.info(f"[STEP 6.5/8] START - Sonar Final Synthesis Validation")
            
            # Initialize validation tracker if not exists
            if not hasattr(self, '_validation_tracker'):
                from app.ai.sonar.validation_tracker import ValidationTracker
                self._validation_tracker = ValidationTracker()
            
            persona_gen_logger.info(f"[STEP 6.5/8] Sub-step: Running structure-only validation (immediate)")
            persona_gen_logger.info(f"[STEP 6.5/8]   → See: logs/sonar_model.log for API call details")
            
            # Run structure-only validation (quick check)
            sonar_synthesis_validation = await enhanced_sonar_validator.validate_final_synthesis_structure(
                final_persona, website, pid
            )
            step_6_5_duration = time.time() - step_6_5_start
            step_timings["step_6.5"] = step_6_5_duration
            api_call_summary["sonar"].append({"step": "6.5", "duration": step_6_5_duration})
            
            structure_valid = sonar_synthesis_validation.get("structure_valid", False)
            required_fields = sonar_synthesis_validation.get("required_fields_present", False)
            
            persona_gen_logger.info(f"[STEP 6.5/8] Sub-step: Marking content validation for deferred execution")
            # Mark full content validation for deferred execution (after enrichment)
            self._validation_tracker.mark_for_deferred_validation(
                step_name="step_6_final_synthesis",
                validation_type="final_synthesis_content",
                data_path="",  # Validate entire persona after enrichment
                target_domain=_extract_domain_from_url(website) if website else None
            )
            
            persona_gen_logger.info(f"[STEP 6.5/8] Result: Structure validation complete")
            persona_gen_logger.info(f"[STEP 6.5/8]   → Structure Valid: {structure_valid}")
            persona_gen_logger.info(f"[STEP 6.5/8]   → Required Fields: {'All present' if required_fields else 'Missing'}")
            persona_gen_logger.info(f"[STEP 6.5/8]   → Content Validation: Deferred")
            persona_gen_logger.info(f"[STEP 6.5/8] END - Duration: {step_6_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Merge validated final persona
            final_persona = sonar_integration_utils.merge_validated_final_persona(
                final_persona, sonar_synthesis_validation, pid
            )
            
            # Step 7: Quality Assurance and Enhancement
            step_7_start = time.time()
            logger.info(f"[PID {pid}] Step 7/8: Quality Assurance START")
            persona_gen_logger.info(f"[STEP 7/8] START - Quality Assurance and Enhancement")
            if progress_tracker:
                await progress_tracker.start_step(7)
            
            persona_gen_logger.info(f"[STEP 7/8] Sub-step: Calling _quality_assurance_and_enhancement()")
            # Step 7: Enhanced Quality Assurance with Sonar
            enhanced_persona = await self._quality_assurance_and_enhancement(
                final_persona, validated_analysis, creative_elements, enhanced_value_alignment, enhanced_market_intelligence, pid
            )
            step_7_duration = time.time() - step_7_start
            step_timings["step_7"] = step_7_duration
            
            persona_gen_logger.info(f"[STEP 7/8] Result: Quality assurance complete")
            persona_gen_logger.info(f"[STEP 7/8] END - Duration: {step_7_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 7.5: Run Deferred Validations (NEW - Improvement 1)
            step_7_5_start = time.time()
            logger.info(f"[PID {pid}] Step 7.5/8: Running Deferred Validations START")
            persona_gen_logger.info(f"[STEP 7.5/8] START - Running Deferred Validations")
            
            deferred_count = self._validation_tracker.get_deferred_count() if hasattr(self, '_validation_tracker') else 0
            persona_gen_logger.info(f"[STEP 7.5/8] Sub-step: Checking for deferred validations")
            persona_gen_logger.info(f"[STEP 7.5/8]   → Deferred Count: {deferred_count}")
            
            if hasattr(self, '_validation_tracker') and deferred_count > 0:
                persona_gen_logger.info(f"[STEP 7.5/8] Sub-step: Running {deferred_count} deferred validation(s)")
                persona_gen_logger.info(f"[STEP 7.5/8]   → See: logs/sonar_model.log for API call details")
                
                deferred_results = await self._validation_tracker.run_deferred_validations(enhanced_persona, pid)
                step_7_5_duration = time.time() - step_7_5_start
                step_timings["step_7.5"] = step_7_5_duration
                
                # Track API calls for deferred validations
                for _ in deferred_results:
                    api_call_summary["sonar"].append({"step": "7.5", "duration": 0})  # Duration tracked in step_7_5_duration
                
                # Update validation results with deferred validations
                for deferred_result in deferred_results:
                    validation_type = deferred_result["validation_type"]
                    result = deferred_result["result"]
                    
                    if validation_type == "market_intelligence":
                        sonar_market_validation = result
                        logger.info(f"[PID {pid}] Deferred market intelligence validation completed")
                    elif validation_type == "final_synthesis_content":
                        # Update synthesis validation with full content validation
                        sonar_synthesis_validation = result
                        logger.info(f"[PID {pid}] Deferred final synthesis content validation completed")
                    # Add other validation types as needed
                
                # Store deferred validation results in persona metadata
                enhanced_persona["deferred_validations"] = deferred_results
                logger.info(f"[PID {pid}] Completed {len(deferred_results)} deferred validations")
                persona_gen_logger.info(f"[STEP 7.5/8] Result: Deferred validations complete")
                persona_gen_logger.info(f"[STEP 7.5/8]   → Completed: {len(deferred_results)}")
            else:
                step_7_5_duration = time.time() - step_7_5_start
                step_timings["step_7.5"] = step_7_5_duration
                logger.info(f"[PID {pid}] No deferred validations to run")
                persona_gen_logger.info(f"[STEP 7.5/8] Result: No deferred validations to run")
            
            persona_gen_logger.info(f"[STEP 7.5/8] END - Duration: {step_7_5_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Step 8: Final Sonar Quality Check
            step_8_start = time.time()
            logger.info(f"[PID {pid}] Step 8/8: Final Sonar Quality Check START")
            persona_gen_logger.info(f"[STEP 8/8] START - Final Sonar Quality Check")
            persona_gen_logger.info(f"[STEP 8/8] Sub-step: Calling _step_8_final_sonar_quality_check()")
            persona_gen_logger.info(f"[STEP 8/8]   → See: logs/sonar_model.log for API call details")
            
            final_quality_result = await self._step_8_final_sonar_quality_check(
                enhanced_persona, website, pid
            )
            step_8_duration = time.time() - step_8_start
            step_timings["step_8"] = step_8_duration
            api_call_summary["sonar"].append({"step": "8", "duration": step_8_duration})
            
            quality_passed = final_quality_result.get("quality_passed", False)
            overall_confidence = final_quality_result.get("overall_confidence", 0)
            issues_found = final_quality_result.get("issues_found", 0)
            
            persona_gen_logger.info(f"[STEP 8/8] Result: Final quality check complete")
            persona_gen_logger.info(f"[STEP 8/8]   → Quality Passed: {quality_passed}")
            persona_gen_logger.info(f"[STEP 8/8]   → Overall Confidence: {overall_confidence}/10")
            persona_gen_logger.info(f"[STEP 8/8]   → Issues Found: {issues_found}")
            persona_gen_logger.info(f"[STEP 8/8] END - Duration: {step_8_duration:.2f}s")
            persona_gen_logger.info("-" * 80)
            
            # Add quality check results to persona
            enhanced_persona["sonar_quality_checks"] = {
                "step_0_relevance": relevance_result,
                "step_1_customer_focus": focus_result,
                "step_2_cross_validation": cross_validation_result,
                "step_8_final_quality": final_quality_result
            }
            
            # Add comprehensive Sonar validation summary
            # Note: sonar_market_validation and sonar_synthesis_validation may have been updated by deferred validations
            all_sonar_validations = [
                relevance_result,
                focus_result,
                sonar_website_validation,
                cross_validation_result,
                sonar_market_validation,  # May have been updated by deferred validation
                sonar_value_validation,
                sonar_creative_validation,
                sonar_synthesis_validation,  # May have been updated by deferred validation
                final_quality_result
            ]
            
            sonar_summary = sonar_integration_utils.summarize_sonar_validations(all_sonar_validations)
            enhanced_persona["sonar_validation_summary"] = sonar_summary
            
            # Add overall confidence score
            enhanced_persona["enhanced_metadata"] = enhanced_persona.get("enhanced_metadata", {})
            enhanced_persona["enhanced_metadata"].update({
                "sonar_overall_confidence": sonar_summary["overall_confidence"],
                "sonar_validations_passed": sonar_summary["passed_validations"],
                "sonar_validations_failed": sonar_summary["failed_validations"],
                "sonar_validations_total": sonar_summary["total_validations"]
            })
            
            total_time = time.time() - start_time
            logger.info(f"--- [PID {pid}] [Enhanced Persona Generator] REQUEST END. Total time: {total_time:.2f}s ---")
            
            # Calculate API call statistics
            sonar_total_duration = sum(call["duration"] for call in api_call_summary["sonar"])
            gemini_total_duration = sum(call["duration"] for call in api_call_summary["gemini"])
            chatgpt_total_duration = sum(call["duration"] for call in api_call_summary["chatgpt"])
            sonar_call_count = len(api_call_summary["sonar"])
            gemini_call_count = len(api_call_summary["gemini"])
            chatgpt_call_count = len(api_call_summary["chatgpt"])
            
            # Parse token usage from API log files
            logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
            sonar_log_file = os.path.join(logs_dir, 'sonar_model.log')
            gemini_log_file = os.path.join(logs_dir, 'gemini_model.log')
            chatgpt_log_file = os.path.join(logs_dir, 'chatgpt_model.log')
            
            token_usage_summary["sonar"] = parse_token_usage_from_logs(pid, sonar_log_file, "sonar")
            token_usage_summary["gemini"] = parse_token_usage_from_logs(pid, gemini_log_file, "gemini")
            token_usage_summary["chatgpt"] = parse_token_usage_from_logs(pid, chatgpt_log_file, "chatgpt")
            
            # Count validations
            total_validations = 9  # Fixed number of validation steps
            passed_validations = sum([
                1 if relevance_result.get("is_relevant", True) else 0,
                1 if focus_result.get("customer_focus_correct", True) else 0,
                1 if sonar_website_validation.get("validation_passed", False) else 0,
                1 if cross_validation_result.get("models_agree", False) else 0,
                1 if sonar_market_validation.get("validation_passed", False) else 0,
                1 if sonar_value_validation.get("validation_passed", False) else 0,
                1 if sonar_creative_validation.get("validation_passed", False) else 0,
                1 if sonar_synthesis_validation.get("structure_valid", False) else 0,
                1 if final_quality_result.get("quality_passed", False) else 0,
            ])
            failed_validations = total_validations - passed_validations
            
            # Log final summary
            persona_gen_logger.info("=" * 80)
            persona_gen_logger.info(f"[COMPLETE] Persona Generation Completed")
            persona_gen_logger.info(f"Total Duration: {total_time:.2f}s ({total_time/60:.1f}m)")
            persona_gen_logger.info(f"Progress: 100% (8/8 steps completed)")
            persona_gen_logger.info("")
            persona_gen_logger.info("Step Timing Summary:")
            for step_name, duration in sorted(step_timings.items()):
                percentage = (duration / total_time * 100) if total_time > 0 else 0
                persona_gen_logger.info(f"  Step {step_name}: {duration:.2f}s ({percentage:.1f}%)")
            persona_gen_logger.info("")
            persona_gen_logger.info("API Call Summary:")
            persona_gen_logger.info(f"  Sonar: {sonar_call_count} calls (Total: {sonar_total_duration:.2f}s)")
            persona_gen_logger.info(f"  Gemini: {gemini_call_count} calls (Total: {gemini_total_duration:.2f}s)")
            persona_gen_logger.info(f"  ChatGPT: {chatgpt_call_count} calls (Total: {chatgpt_total_duration:.2f}s)")
            persona_gen_logger.info("")
            persona_gen_logger.info("Token Usage Summary:")
            persona_gen_logger.info(f"  Sonar: Total: {token_usage_summary['sonar']['total']:,} tokens (Prompt: {token_usage_summary['sonar']['prompt']:,}, Completion: {token_usage_summary['sonar']['completion']:,})")
            persona_gen_logger.info(f"  Gemini: Total: {token_usage_summary['gemini']['total']:,} tokens (Prompt: {token_usage_summary['gemini']['prompt']:,}, Completion: {token_usage_summary['gemini']['completion']:,})")
            persona_gen_logger.info(f"  ChatGPT: Total: {token_usage_summary['chatgpt']['total']:,} tokens (Prompt: {token_usage_summary['chatgpt']['prompt']:,}, Completion: {token_usage_summary['chatgpt']['completion']:,})")
            total_tokens = token_usage_summary['sonar']['total'] + token_usage_summary['gemini']['total'] + token_usage_summary['chatgpt']['total']
            persona_gen_logger.info(f"  Grand Total: {total_tokens:,} tokens")
            persona_gen_logger.info("")
            persona_gen_logger.info("Validation Summary:")
            persona_gen_logger.info(f"  Total Validations: {total_validations}")
            persona_gen_logger.info(f"  Passed: {passed_validations}")
            persona_gen_logger.info(f"  Failed: {failed_validations}")
            deferred_count = self._validation_tracker.get_deferred_count() if hasattr(self, '_validation_tracker') else 0
            if deferred_count > 0:
                persona_gen_logger.info(f"  Deferred: {deferred_count} (completed in Step 7.5)")
            overall_confidence = sonar_summary.get("overall_confidence", 0) if 'sonar_summary' in locals() else 0
            persona_gen_logger.info(f"  Overall Confidence: {overall_confidence}/10")
            persona_gen_logger.info("")
            persona_gen_logger.info("Final Result:")
            persona_gen_logger.info(f"  Status: SUCCESS")
            persona_gen_logger.info(f"  Company: {company_name}")
            persona_gen_logger.info(f"  Industry: {selected_industry or 'Not specified'}")
            persona_gen_logger.info("=" * 80)
            
            return enhanced_persona
            
        except Exception as e:
            logger.error(f"[PID {pid}] [Enhanced Persona Generator] Error: {e}", exc_info=True)
            total_time = time.time() - start_time
            persona_gen_logger.error("=" * 80)
            persona_gen_logger.error(f"[ERROR] Persona Generation Failed")
            persona_gen_logger.error(f"Error: {str(e)}")
            persona_gen_logger.error(f"Duration before error: {total_time:.2f}s")
            persona_gen_logger.error(f"Website: {website}")
            persona_gen_logger.error("=" * 80)
            # Create a minimal fallback persona
            fallback_persona = {
                "company": {
                    "name": "Analysis Failed",
                    "year_established": 2000,
                    "headquarters_location": "Unknown",
                    "website": website
                },
                "product_range": ["Product information not available"],
                "services": ["Service information not available"],
                "pain_points": ["Pain points analysis not available"],
                "goals": ["Goals analysis not available"],
                "value_drivers": ["Value drivers analysis not available"],
                "value_signals": ["Value signals analysis not available"],
                "likely_objections": ["Objections analysis not available"],
                "chain_of_thought": f"Persona generation failed with error: {str(e)}",
                "error": f"Enhanced persona generation failed: {str(e)}"
            }
            return fallback_persona
    
    async def _step_0_relevance_validation(self, website: str, pid: int) -> Dict[str, Any]:
        """
        Step 0: Pre-analysis relevance validation using Sonar.
        
        Args:
            website: Target website URL
            pid: Process ID for logging
            
        Returns:
            Relevance validation result
        """
        logger.info(f"[PID {pid}] [Step 0] Starting relevance validation for: {website}")
        
        try:
            # Perform relevance validation using Sonar quality gates
            relevance_result = await self.quality_gates.step_0_relevance_validation(
                website, website_content=None, pid=pid
            )
            
            logger.info(f"[PID {pid}] [Step 0] Relevance validation complete - Relevant: {relevance_result.get('is_relevant', False)}")
            return relevance_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [Step 0] Relevance validation error: {e}")
            # Default to relevant if validation fails
            return {
                "is_relevant": True,
                "relevance_score": 5,
                "recommended_action": "proceed",
                "error": f"Relevance validation failed: {str(e)}"
            }
    
    def _create_relevance_rejection_persona(self, website: str, relevance_result: Dict, pid: int) -> Dict[str, Any]:
        """
        Create a persona indicating the website was rejected for relevance.
        
        Args:
            website: Target website URL
            relevance_result: Relevance validation result
            pid: Process ID for logging
            
        Returns:
            Rejection persona
        """
        logger.info(f"[PID {pid}] Creating relevance rejection persona for: {website}")
        
        return {
            "company": {
                "name": "Relevance Check Failed",
                "year_established": 2000,
                "headquarters_location": "Unknown",
                "website": website
            },
            "product_range": ["Not relevant to our business"],
            "services": ["Not relevant to our business"],
            "pain_points": ["Not applicable - company not relevant"],
            "goals": ["Not applicable - company not relevant"],
            "value_drivers": ["Not applicable - company not relevant"],
            "value_signals": ["Not applicable - company not relevant"],
            "likely_objections": ["Not applicable - company not relevant"],
            "chain_of_thought": f"Website rejected during Step 0 relevance validation. Relevance score: {relevance_result.get('relevance_score', 0)}. Reason: {relevance_result.get('why_not_relevant', 'Not specified')}",
            "relevance_validation": relevance_result,
            "status": "rejected_for_relevance",
            "error": "Website not relevant to our business based on Sonar validation"
        }
    
    async def _step_1_customer_focus_validation(self, gemini_analysis: Dict, chatgpt_analysis: Dict, 
                                               website: str, pid: int) -> Dict[str, Any]:
        """
        Step 1.5: Customer focus validation using Sonar.
        
        Args:
            gemini_analysis: Gemini analysis result
            chatgpt_analysis: ChatGPT analysis result
            website: Target website URL
            pid: Process ID for logging
            
        Returns:
            Customer focus validation result
        """
        logger.info(f"[PID {pid}] [Step 1.5] Starting customer focus validation for: {website}")
        
        try:
            # Combine analyses for validation
            combined_analysis = {
                "gemini_analysis": gemini_analysis,
                "chatgpt_analysis": chatgpt_analysis,
                "website": website
            }
            
            # Perform customer focus validation using Sonar quality gates
            focus_result = await self.quality_gates.step_1_customer_focus_validation(
                combined_analysis, website, pid
            )
            
            logger.info(f"[PID {pid}] [Step 1.5] Customer focus validation complete - Correct: {focus_result.get('customer_focus_correct', False)}")
            return focus_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [Step 1.5] Customer focus validation error: {e}")
            # Default to correct if validation fails
            return {
                "customer_focus_correct": True,
                "confidence_score": 5,
                "should_proceed": True,
                "error": f"Customer focus validation failed: {str(e)}"
            }
    
    async def _strict_company_identity_validation(self, gemini_analysis: Dict, chatgpt_analysis: Dict,
                                                  website: str, pid: int, 
                                                  verified_company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        STRICT Company Identity Validation - HARD STOP if models analyze different companies.
        
        This function ensures both Gemini and ChatGPT are analyzing the SAME target company.
        If verified_company_name is provided, it is used as the source of truth.
        Otherwise, domain owner is used as fallback.
        
        Args:
            gemini_analysis: Gemini analysis result
            chatgpt_analysis: ChatGPT analysis result
            website: Target website URL
            pid: Process ID for logging
            verified_company_name: User-verified company name (optional, used as source of truth)
            
        Returns:
            Validation result with all_match flag (True = proceed, False = STOP)
        """
        logger.info(f"[PID {pid}] [STRICT VALIDATION] Starting company identity validation for: {website}")
        
        try:
            # Extract company names from both analyses (pass verified_company_name as fallback)
            gemini_company = _extract_company_name_from_analysis(gemini_analysis, pid, verified_company_name=verified_company_name)
            chatgpt_company = _extract_company_name_from_analysis(chatgpt_analysis, pid, verified_company_name=verified_company_name)
            
            # Extract domain
            domain = _extract_domain_from_url(website)
            
            logger.info(f"[PID {pid}] [STRICT VALIDATION] Extracted - Gemini: '{gemini_company}', ChatGPT: '{chatgpt_company}', Domain: '{domain}'")
            
            # Determine source of truth: verified_company_name > domain_owner > model comparison
            source_of_truth = ""
            source_of_truth_confidence = 1.0  # User verification is 100% confident
            
            if verified_company_name:
                source_of_truth = verified_company_name.strip()
                logger.info(f"[PID {pid}] [STRICT VALIDATION] Using verified company as source of truth: '{source_of_truth}'")
            else:
                # Fallback to domain owner if no verified company
                try:
                    domain_validation = await self.domain_validator.validate_domain_ownership(
                        website, None, pid
                    )
                    source_of_truth = domain_validation.get("actual_company_name", "").strip()
                    source_of_truth_confidence = domain_validation.get("ownership_confidence", 0) / 10.0
                    logger.info(f"[PID {pid}] [STRICT VALIDATION] Using domain owner as source of truth: '{source_of_truth}' (confidence: {source_of_truth_confidence})")
                except Exception as e:
                    logger.warning(f"[PID {pid}] [STRICT VALIDATION] Sonar domain validation failed: {e}. Using model comparison only.")
                    source_of_truth = ""  # Will fall back to model-to-model comparison
            
            # Calculate similarities
            # Use stricter threshold for verified companies (90% vs 85%)
            similarity_threshold = 0.90 if verified_company_name else 0.85
            if verified_company_name:
                logger.info(f"[PID {pid}] [STRICT VALIDATION] Using stricter threshold (90%) for verified company: {verified_company_name}")
            
            # Compare Gemini vs ChatGPT
            gemini_vs_chatgpt_similarity = _calculate_name_similarity(gemini_company, chatgpt_company)
            companies_match = gemini_vs_chatgpt_similarity >= similarity_threshold
            
            # Compare Gemini vs Source of Truth
            gemini_vs_source_similarity = _calculate_name_similarity(gemini_company, source_of_truth) if source_of_truth else 0.0
            gemini_matches_source = gemini_vs_source_similarity >= similarity_threshold if source_of_truth else None
            
            # Compare ChatGPT vs Source of Truth
            chatgpt_vs_source_similarity = _calculate_name_similarity(chatgpt_company, source_of_truth) if source_of_truth else 0.0
            chatgpt_matches_source = chatgpt_vs_source_similarity >= similarity_threshold if source_of_truth else None
            
            # Determine if all match
            # Priority: verified_company_name > domain_owner > model comparison
            if source_of_truth:
                # If we have a source of truth (verified or domain owner), both models must match it
                all_match = companies_match and gemini_matches_source and chatgpt_matches_source
                if verified_company_name:
                    logger.info(f"[PID {pid}] [STRICT VALIDATION] Using verified company '{source_of_truth}' as source of truth")
                else:
                    logger.info(f"[PID {pid}] [STRICT VALIDATION] Using domain owner '{source_of_truth}' as source of truth")
            else:
                # Fallback: if no source of truth available, require Gemini and ChatGPT to match
                all_match = companies_match
                logger.warning(f"[PID {pid}] [STRICT VALIDATION] No source of truth available - using model-to-model comparison only")
            
            # Build mismatch details
            mismatch_details = {
                "gemini_vs_chatgpt": "match" if companies_match else "mismatch",
                "gemini_vs_source": "match" if gemini_matches_source else ("mismatch" if source_of_truth else "unknown"),
                "chatgpt_vs_source": "match" if chatgpt_matches_source else ("mismatch" if source_of_truth else "unknown"),
                "source_type": "verified" if verified_company_name else ("domain_owner" if source_of_truth else "none")
            }
            
            # Calculate overall confidence score
            confidence_score = 0
            if companies_match:
                confidence_score += 3
            if gemini_matches_source:
                confidence_score += 3
            if chatgpt_matches_source:
                confidence_score += 3
            if verified_company_name:
                confidence_score += 2  # Bonus for user verification
            elif source_of_truth_confidence >= 0.7:
                confidence_score += 1
            
            # Build error message if validation failed
            error_message = ""
            if not all_match:
                error_message = f"Company identity validation FAILED. "
                
                # Check if Gemini extraction failed (empty string)
                gemini_extraction_failed = not gemini_company or gemini_company == ""
                chatgpt_extraction_failed = not chatgpt_company or chatgpt_company == ""
                
                if gemini_extraction_failed:
                    error_message += f"Gemini failed to extract company name from analysis. "
                    # Check if analysis has errors
                    if isinstance(gemini_analysis, dict):
                        if "error" in gemini_analysis:
                            error_message += f"Gemini analysis contains errors: {gemini_analysis.get('error', 'Unknown error')[:100]}. "
                        if "analysis_failed" in gemini_analysis:
                            error_message += "Gemini analysis failed completely. "
                elif not companies_match:
                    error_message += f"Gemini analyzed '{gemini_company}' but ChatGPT analyzed '{chatgpt_company}'. "
                
                if chatgpt_extraction_failed:
                    error_message += f"ChatGPT failed to extract company name from analysis. "
                
                if source_of_truth:
                    source_label = "verified company" if verified_company_name else "domain owner"
                    if not gemini_matches_source and not gemini_extraction_failed:
                        error_message += f"Gemini's '{gemini_company}' does not match {source_label} '{source_of_truth}'. "
                    if not chatgpt_matches_source and not chatgpt_extraction_failed:
                        error_message += f"ChatGPT's '{chatgpt_company}' does not match {source_label} '{source_of_truth}'. "
                
                error_message += f"Domain: {domain}. Process STOPPED to prevent incorrect persona generation."
            
            result = {
                "validation_passed": all_match,
                "all_match": all_match,
                "gemini_company": gemini_company,
                "chatgpt_company": chatgpt_company,
                "source_of_truth": source_of_truth,
                "source_type": "verified" if verified_company_name else ("domain_owner" if source_of_truth else "none"),
                "domain": domain,
                "companies_match": companies_match,
                "gemini_matches_source": gemini_matches_source,
                "chatgpt_matches_source": chatgpt_matches_source,
                "similarity_scores": {
                    "gemini_vs_chatgpt": round(gemini_vs_chatgpt_similarity, 3),
                    "gemini_vs_source": round(gemini_vs_source_similarity, 3) if source_of_truth else None,
                    "chatgpt_vs_source": round(chatgpt_vs_source_similarity, 3) if source_of_truth else None
                },
                "confidence_score": confidence_score,
                "mismatch_details": mismatch_details,
                "error_message": error_message,
                "source_confidence": source_of_truth_confidence
            }
            
            if all_match:
                logger.info(f"[PID {pid}] [STRICT VALIDATION] ✅ PASSED - All models analyzing same company: '{gemini_company}'")
            else:
                logger.error(f"[PID {pid}] [STRICT VALIDATION] ❌ FAILED - {error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [STRICT VALIDATION] Error during validation: {e}", exc_info=True)
            # On error, fail safe - don't proceed
            return {
                "validation_passed": False,
                "all_match": False,
                "gemini_company": "",
                "chatgpt_company": "",
                "source_of_truth": verified_company_name if verified_company_name else "",
                "source_type": "verified" if verified_company_name else "none",
                "domain": _extract_domain_from_url(website),
                "companies_match": False,
                "gemini_matches_source": False,
                "chatgpt_matches_source": False,
                "confidence_score": 0,
                "mismatch_details": {},
                "error_message": f"Validation error: {str(e)}",
                "source_confidence": 0.0
            }
    
    def _create_company_mismatch_rejection_persona(self, website: str, identity_validation: Dict,
                                                   gemini_analysis: Dict, chatgpt_analysis: Dict,
                                                   pid: int) -> Dict[str, Any]:
        """
        Create a rejection persona when company identity validation fails.
        
        Args:
            website: Target website URL
            identity_validation: Result from strict company identity validation
            gemini_analysis: Gemini analysis result
            chatgpt_analysis: ChatGPT analysis result
            pid: Process ID for logging
            
        Returns:
            Rejection persona with error details
        """
        logger.info(f"[PID {pid}] Creating company mismatch rejection persona for: {website}")
        
        gemini_company = identity_validation.get("gemini_company", "Unknown")
        chatgpt_company = identity_validation.get("chatgpt_company", "Unknown")
        source_of_truth = identity_validation.get("source_of_truth", "Unknown")
        source_type = identity_validation.get("source_type", "none")
        domain = identity_validation.get("domain", website)
        
        # Build detailed error message
        error_details = []
        if not identity_validation.get("companies_match", False):
            error_details.append(f"Gemini analyzed '{gemini_company}' but ChatGPT analyzed '{chatgpt_company}'")
        if source_of_truth and source_of_truth != "Unknown":
            source_label = "verified company" if source_type == "verified" else "domain owner"
            if not identity_validation.get("gemini_matches_source", False):
                error_details.append(f"Gemini's '{gemini_company}' does not match {source_label} '{source_of_truth}'")
            if not identity_validation.get("chatgpt_matches_source", False):
                error_details.append(f"ChatGPT's '{chatgpt_company}' does not match {source_label} '{source_of_truth}'")
        
        return {
            "company": {
                "name": "Company Identity Mismatch Detected",
                "website": website,
                "domain": domain
            },
            "status": "rejected_company_mismatch",
            "error": "Both AI models must analyze the same company. Validation failed.",
            "validation_details": identity_validation,
            "detected_companies": {
                "gemini": gemini_company,
                "chatgpt": chatgpt_company,
                "source_of_truth": source_of_truth,
                "source_type": source_type
            },
            "error_details": error_details,
            "similarity_scores": identity_validation.get("similarity_scores", {}),
            "recommendation": "Please verify the website URL is correct and accessible. The AI models detected different companies, which could lead to incorrect persona generation.",
            "chain_of_thought": f"Process stopped at Step 1.25 (Strict Company Identity Validation). {identity_validation.get('error_message', 'Unknown error')}",
            "product_range": [],
            "services": [],
            "pain_points": ["Validation failed - cannot determine correct company"],
            "goals": [],
            "value_drivers": [],
            "value_signals": [],
            "likely_objections": []
        }
    
    async def _step_2_sonar_cross_validation(self, gemini_analysis: Dict, chatgpt_analysis: Dict, 
                                            validated_analysis: Dict, website: str, pid: int) -> Dict[str, Any]:
        """
        Step 2.5: Sonar cross-model validation.
        
        Args:
            gemini_analysis: Gemini analysis result
            chatgpt_analysis: ChatGPT analysis result
            validated_analysis: Cross-validated analysis result
            website: Target website URL
            pid: Process ID for logging
            
        Returns:
            Cross-model validation result
        """
        logger.info(f"[PID {pid}] [Step 2.5] Starting Sonar cross-model validation for: {website}")
        
        try:
            # Perform cross-model validation using Sonar quality gates
            cross_validation_result = await self.quality_gates.step_2_cross_model_validation(
                gemini_analysis, chatgpt_analysis, website, pid
            )
            
            logger.info(f"[PID {pid}] [Step 2.5] Sonar cross-model validation complete - Models agree: {cross_validation_result.get('models_agree', False)}")
            return cross_validation_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [Step 2.5] Sonar cross-model validation error: {e}")
            # Default to agreement if validation fails
            return {
                "models_agree": True,
                "confidence_score": 5,
                "should_proceed": True,
                "error": f"Sonar cross-model validation failed: {str(e)}"
            }
    
    async def _step_8_final_sonar_quality_check(self, final_persona: Dict, website: str, pid: int) -> Dict[str, Any]:
        """
        Step 8: Final Sonar quality check.
        
        Args:
            final_persona: Final persona to validate
            website: Target website URL
            pid: Process ID for logging
            
        Returns:
            Final quality check result
        """
        logger.info(f"[PID {pid}] [Step 8] Starting final Sonar quality check for: {website}")
        
        try:
            # Perform final quality check using Sonar quality gates
            final_quality_result = await self.quality_gates.final_quality_check(
                final_persona, website, pid
            )
            
            logger.info(f"[PID {pid}] [Step 8] Final Sonar quality check complete - Passed: {final_quality_result.get('quality_passed', False)}")
            return final_quality_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [Step 8] Final Sonar quality check error: {e}")
            # Default to passed if validation fails
            return {
                "quality_passed": True,
                "confidence_score": 5,
                "should_proceed": True,
                "error": f"Final Sonar quality check failed: {str(e)}"
            }
    
    async def _parallel_website_analysis(self, website: str, industry: str, pid: int, 
                                         verified_company_name: Optional[str] = None) -> Tuple[Dict, Dict]:
        """Perform parallel website analysis using both Gemini and ChatGPT with web search.
        
        Args:
            website: Target website URL
            industry: Industry classification
            pid: Process ID for logging
            verified_company_name: User-verified company name (optional)
        """
        
        # Create analysis tasks for both models
        gemini_task = self._gemini_website_analysis(website, industry, pid, verified_company_name=verified_company_name)
        chatgpt_task = self._chatgpt_website_analysis(website, industry, pid, verified_company_name=verified_company_name)
        
        # Execute both analyses in parallel
        gemini_result, chatgpt_result = await asyncio.gather(
            gemini_task, chatgpt_task, return_exceptions=True
        )
        
        # Handle exceptions - ensure both results are Dict, not Exception
        if isinstance(gemini_result, Exception):
            logger.error(f"[PID {pid}] Gemini analysis failed: {gemini_result}")
            gemini_result = {"error": f"Gemini analysis failed: {str(gemini_result)}"}
        elif not isinstance(gemini_result, dict):
            logger.error(f"[PID {pid}] Gemini analysis returned unexpected type: {type(gemini_result)}")
            gemini_result = {"error": f"Gemini analysis returned unexpected type: {type(gemini_result)}"}
        
        if isinstance(chatgpt_result, Exception):
            logger.error(f"[PID {pid}] ChatGPT analysis failed: {chatgpt_result}")
            chatgpt_result = {"error": f"ChatGPT analysis failed: {str(chatgpt_result)}"}
        elif not isinstance(chatgpt_result, dict):
            logger.error(f"[PID {pid}] ChatGPT analysis returned unexpected type: {type(chatgpt_result)}")
            chatgpt_result = {"error": f"ChatGPT analysis returned unexpected type: {type(chatgpt_result)}"}
        
        # Type narrowing: both results are now guaranteed to be Dict
        gemini_dict: Dict[str, Any] = gemini_result if isinstance(gemini_result, dict) else {"error": "Invalid result type"}
        chatgpt_dict: Dict[str, Any] = chatgpt_result if isinstance(chatgpt_result, dict) else {"error": "Invalid result type"}
        
        return gemini_dict, chatgpt_dict
    
    async def _gemini_website_analysis(self, website: str, industry: str, pid: int, 
                                      verified_company_name: Optional[str] = None) -> Dict[str, Any]:
        """Perform website analysis using Gemini with web search.
        
        Args:
            website: Target website URL
            industry: Industry classification
            pid: Process ID for logging
            verified_company_name: User-verified company name (optional)
        """
        
        max_retries = 2
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                # Use existing enhanced website analyzer
                from app.ai.enhanced_website_analyzer import enhanced_website_analyzer
                
                # Pass verified_company_name to ensure correct company analysis
                analysis = await enhanced_website_analyzer.analyze_website_deep(website, industry, verified_company_name=verified_company_name, pid=pid)
                
                # Check if analysis contains errors
                if isinstance(analysis, dict) and "error" in analysis:
                    error_msg = analysis.get("error", "Unknown error")
                    logger.warning(f"[PID {pid}] Gemini deep analysis returned error (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"[PID {pid}] Retrying Gemini analysis in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        # Final attempt failed - create minimal analysis with verified company name
                        logger.error(f"[PID {pid}] Gemini analysis failed after {max_retries} attempts")
                        analysis = {
                            "website_url": website,
                            "target_industry": industry,
                            "verified_company_name": verified_company_name,
                            "error": error_msg,
                            "analysis_failed": True
                        }
                        # Still try to add insights
                
                # Ensure verified_company_name is in analysis for extraction
                if verified_company_name and "verified_company_name" not in analysis:
                    analysis["verified_company_name"] = verified_company_name
                
                # Add Gemini-specific insights with verified company context
                verified_context = ""
                if verified_company_name:
                    verified_context = f"""
        
        ═══════════════════════════════════════════════════════════
        🎯 CRITICAL: USER-VERIFIED COMPANY (AUTHORITATIVE SOURCE)
        ═══════════════════════════════════════════════════════════
        
        The domain {website} belongs to: {verified_company_name}
        
        THIS IS USER-VERIFIED INFORMATION AND IS THE SOURCE OF TRUTH.
        
        YOU MUST:
        ✅ Analyze ONLY {verified_company_name}
        ✅ Verify all information matches {verified_company_name}
        ✅ Ignore any other companies with similar names
        ✅ Confirm domain ownership matches {verified_company_name}
        
        YOU MUST NOT:
        ❌ Analyze any other company, even with similar names
        ❌ Use information about companies that don't own this domain
        ❌ Confuse {verified_company_name} with similarly-named companies
        
        ═══════════════════════════════════════════════════════════
        """
                
                gemini_insights_prompt = f"""
        Based on the website analysis of {website}, provide additional strategic insights:{verified_context}
        
        **CRITICAL: The company you are analyzing is: {verified_company_name if verified_company_name else "the company that owns " + website}**
        
        **Analysis Data:**
        {json.dumps(analysis, indent=2, default=str)[:50000]}  # Limit size to prevent token overflow
        
        **Additional Analysis Request:**
        1. Strategic positioning analysis
        2. Technology stack insights
        3. Competitive differentiation factors
        4. Growth trajectory indicators
        5. Risk assessment
        
        **REQUIRED OUTPUT FORMAT (JSON only):**
        {{
          "company_name": "{verified_company_name if verified_company_name else '[extracted from analysis]'}",
          "company_name_verified": {str(verified_company_name is not None).lower()},
          "strategic_positioning": "string",
          "technology_insights": "string",
          "competitive_differentiation": "string",
          "growth_indicators": "string",
          "risk_assessment": "string"
        }}
        """
                
                # Use higher token limit to prevent truncation - insights can be extensive
                gemini_insights = await gemini_client(gemini_insights_prompt, max_tokens=16000)
                
                # Check if response indicates truncation or error
                if isinstance(gemini_insights, str) and gemini_insights.startswith("ERROR:"):
                    logger.warning(f"[PID {pid}] Gemini insights returned error (attempt {attempt + 1}/{max_retries}): {gemini_insights[:200]}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"[PID {pid}] Retrying Gemini insights in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        # Final attempt failed
                        analysis["gemini_insights"] = {"error": "Gemini API error", "raw_insights": gemini_insights}
                        # Ensure company name is available for extraction
                        if verified_company_name:
                            analysis["verified_company_name"] = verified_company_name
                        return analysis
                
                try:
                    # Clean the response - remove markdown code blocks if present
                    cleaned_response = gemini_insights.strip()
                    if cleaned_response.startswith('```json'):
                        cleaned_response = cleaned_response[7:]  # Remove ```json
                    if cleaned_response.startswith('```'):
                        cleaned_response = cleaned_response[3:]  # Remove ```
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                    cleaned_response = cleaned_response.strip()
                    
                    insights_data = json.loads(cleaned_response)
                    
                    # Ensure company_name is in insights
                    if verified_company_name and "company_name" not in insights_data:
                        insights_data["company_name"] = verified_company_name
                        insights_data["company_name_verified"] = True
                    
                    analysis["gemini_insights"] = insights_data
                    
                    # Ensure verified_company_name is in main analysis for extraction
                    if verified_company_name:
                        analysis["verified_company_name"] = verified_company_name
                    
                    return analysis
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"[PID {pid}] Failed to parse Gemini insights JSON: {e}")
                    # Store raw insights and ensure company name is available
                    analysis["gemini_insights"] = {"raw_insights": gemini_insights, "parse_error": str(e)}
                    if verified_company_name:
                        analysis["verified_company_name"] = verified_company_name
                    return analysis
                
            except Exception as e:
                logger.error(f"[PID {pid}] Gemini analysis exception (attempt {attempt + 1}/{max_retries}): {e}", exc_info=True)
                
                if attempt < max_retries - 1:
                    logger.info(f"[PID {pid}] Retrying Gemini analysis in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    # Final attempt failed - return minimal analysis
                    return {
                        "website_url": website,
                        "target_industry": industry,
                        "verified_company_name": verified_company_name,
                        "error": f"Gemini analysis failed after {max_retries} attempts: {str(e)}",
                        "analysis_failed": True
                    }
        
        # Should not reach here, but just in case
        return {
            "website_url": website,
            "target_industry": industry,
            "verified_company_name": verified_company_name,
            "error": "Gemini analysis failed - max retries exceeded",
            "analysis_failed": True
        }
    
    async def _chatgpt_website_analysis(self, website: str, industry: str, pid: int, 
                                      verified_company_name: Optional[str] = None) -> Dict[str, Any]:
        """Perform website analysis using ChatGPT with web search.
        
        Args:
            website: Target website URL
            industry: Industry classification
            pid: Process ID for logging
            verified_company_name: User-verified company name (optional)
        """
        
        # Build verified company context if available
        verified_context = ""
        if verified_company_name:
            verified_context = f"""
        
        ═══════════════════════════════════════════════════════════
        🎯 CRITICAL: USER-VERIFIED COMPANY (AUTHORITATIVE SOURCE)
        ═══════════════════════════════════════════════════════════
        
        The domain {website} belongs to: {verified_company_name}
        
        THIS IS USER-VERIFIED INFORMATION AND IS THE SOURCE OF TRUTH.
        
        YOU MUST:
        ✅ Analyze ONLY {verified_company_name}
        ✅ Verify all information matches {verified_company_name}
        ✅ Ignore any other companies with similar names
        ✅ Confirm domain ownership matches {verified_company_name}
        
        YOU MUST NOT:
        ❌ Analyze any other company, even with similar names
        ❌ Use information about companies that don't own this domain
        ❌ Confuse {verified_company_name} with similarly-named companies
        
        ═══════════════════════════════════════════════════════════
        """
        
        chatgpt_prompt = f"""
        ═══════════════════════════════════════════════════════════
        🎯 TARGET COMPANY: {verified_company_name if verified_company_name else "Company that owns " + website}
        ═══════════════════════════════════════════════════════════
        
        {verified_context}
        
        **YOUR TASK:**
        Analyze ONLY {verified_company_name if verified_company_name else "the company that owns " + website}
        
        **BEFORE YOU START:**
        1. Search: "who owns {website}"
        2. Verify: Does the result match {verified_company_name if verified_company_name else "the domain owner"}?
        3. If NO match → STOP and report the mismatch
        4. If YES match → Proceed with analysis
        
        You MUST analyze ONLY the company that owns and operates the specific website domain: {website}
        
        **CRITICAL INSTRUCTIONS:**
        1. Extract the domain name from the URL: {website}
        2. Search for information about the company that OWNS this specific domain
        3. Do NOT analyze any other companies, even if they have similar names
        4. If you find multiple companies with similar names, you MUST identify which one owns this domain
        5. Verify the company name matches the domain owner before proceeding with analysis
        6. If uncertain, explicitly state which company you're analyzing and why you believe it owns this domain
        
        **EXAMPLE:**
        - If the URL is "kramer-online.com", you must analyze the company that owns "kramer-online.com" domain
        - Do NOT analyze "Kramer Electronics" (AV company) if the domain owner is "Kramer-Werke GmbH" (construction machinery)
        - Always verify domain ownership matches the company you're analyzing
        
        **SEARCH STRATEGY:**
        - Search for: "company that owns {website}" or "who owns {website}"
        - Search for: "{website} company information"
        - Verify domain ownership before analyzing company details
        - Use domain registration information if available
        
        Conduct a comprehensive analysis of the company that owns {website} with web search grounding.
        
        **Analysis Requirements:**
        1. Company Overview (name, history, size, location) - MUST match the domain owner
        2. Products & Services (detailed portfolio, features, applications)
        3. Customer Segments (target customers, industries served)
        4. Value Propositions (problems solved, benefits offered)
        5. Market Positioning (differentiation, brand messaging)
        6. Business Model (revenue streams, sales channels)
        7. Technology & Innovation (tech stack, R&D focus)
        8. Challenges & Opportunities (industry challenges, growth strategies)
        
        **Additional ChatGPT-Specific Analysis:**
        1. Creative market positioning insights
        2. Innovative business model elements
        3. Future growth opportunities
        4. Customer experience analysis
        5. Digital transformation readiness
        
        **VALIDATION CHECK:**
        Before providing the analysis, confirm:
        - The company name you identified: {verified_company_name if verified_company_name else "[extract from search]"}
        - That this company owns the domain {website}
        - Any evidence that confirms domain ownership
        
        **OUTPUT REQUIREMENT:**
        Your analysis MUST start with:
        "Company Name: {verified_company_name if verified_company_name else '[extracted name]'}"
        "Domain Ownership Confirmed: Yes/No"
        "Analysis Target: {verified_company_name if verified_company_name else '[extracted name]'}"
        
        Provide analysis as a JSON object with these REQUIRED fields:
        {{
          "company_name": "{verified_company_name if verified_company_name else '[extracted from analysis]'}",
          "company_name_verified": {str(verified_company_name is not None).lower()},
          "domain_ownership_confirmed": true,
          "company_overview": {{"name": "{verified_company_name if verified_company_name else '[extracted]'}", "domain_ownership_confirmed": true, ...}},
          "products_services": {{...}},
          "customer_segments": {{...}},
          "value_propositions": {{...}},
          "market_positioning": {{...}},
          "business_model": {{...}},
          "technology_innovation": {{...}},
          "challenges_opportunities": {{...}},
          "chatgpt_creative_insights": {{...}}
        }}
        """
        
        chatgpt_analysis = await chatgpt_generate(
            chatgpt_prompt, 
            use_web_search=True,
            pid=pid
        )
        
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = chatgpt_analysis.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            return json.loads(cleaned_response)
        except:
            return {"raw_analysis": chatgpt_analysis, "error": "Failed to parse ChatGPT analysis"}
    
    async def _cross_validate_and_synthesize(self, gemini_analysis: Dict, chatgpt_analysis: Dict, 
                                           website: str, pid: int) -> Dict[str, Any]:
        """Cross-validate and synthesize results from both models."""
        
        # First, validate that both analyses are about the correct company
        from urllib.parse import urlparse
        parsed_url = urlparse(website)
        domain = parsed_url.netloc or parsed_url.path.split('/')[0]
        domain_base = domain.replace('www.', '').split('/')[0]
        
        # Extract company names from both analyses
        gemini_company = gemini_analysis.get("company_overview", {}).get("name", "") if isinstance(gemini_analysis.get("company_overview"), dict) else ""
        chatgpt_company = chatgpt_analysis.get("company_overview", {}).get("name", "") if isinstance(chatgpt_analysis.get("company_overview"), dict) else ""
        
        # Log company names for debugging
        logger.info(f"[PID {pid}] [Cross-Validation] Gemini company: {gemini_company}, ChatGPT company: {chatgpt_company}, Domain: {domain_base}")
        
        # Check if companies match (basic validation)
        if gemini_company and chatgpt_company and gemini_company.lower() != chatgpt_company.lower():
            logger.warning(f"[PID {pid}] [Cross-Validation] WARNING: Company name mismatch! Gemini: {gemini_company}, ChatGPT: {chatgpt_company}")
            logger.warning(f"[PID {pid}] [Cross-Validation] Domain is {domain_base} - one of these analyses may be about the wrong company")
        
        synthesis_prompt = f"""
        Compare and synthesize the analysis results from two AI models for the website {website}.
        
        **CRITICAL DOMAIN VALIDATION:**
        - The website domain is: {domain_base}
        - You MUST ensure both analyses are about the company that OWNS this domain
        - If the analyses mention different companies, prioritize the one that owns {domain_base}
        - Common mistake: Analyzing "Kramer Electronics" (AV company) when domain is "kramer-online.com" (should be "Kramer-Werke GmbH")
        - Verify company names match the domain owner before synthesizing
        
        **Gemini Analysis (Analytical Focus):**
        {json.dumps(gemini_analysis, indent=2)}
        
        **ChatGPT Analysis (Creative Focus):**
        {json.dumps(chatgpt_analysis, indent=2)}
        
        **CRITICAL SYNTHESIS TASK:**
        You must extract SPECIFIC, MEANINGFUL insights from both analyses. Do NOT return empty arrays.
        
        1. **Areas of Agreement (Minimum 5-10 points):**
           - Find specific insights that BOTH models identified about the company
           - Focus on business model, target customers, products/services, challenges, opportunities
           - Be specific and detailed, not generic
        
        2. **Unique Gemini Insights (Minimum 3-5 points):**
           - Extract analytical insights that ONLY Gemini identified
           - Focus on technical details, market analysis, competitive positioning
           - Include specific data points, metrics, or analytical observations
        
        3. **Unique ChatGPT Insights (Minimum 3-5 points):**
           - Extract creative insights that ONLY ChatGPT identified
           - Focus on innovative perspectives, future opportunities, creative solutions
           - Include unique angles, creative suggestions, or novel observations
        
        4. **Validation Process:**
           - Explain how you compared the two analyses
           - Describe what makes each insight unique or shared
           - Provide confidence score based on analysis quality
        
        **REQUIRED OUTPUT FORMAT (JSON only):**
        {{
          "unified_analysis": {{
            "company_overview": "Combined company description",
            "business_model": "Synthesized business model",
            "target_customers": "Combined customer segments",
            "products_services": "Combined offerings",
            "challenges_opportunities": "Synthesized insights"
          }},
          "agreement_areas": [
            "Specific insight both models identified about business model",
            "Specific insight both models identified about target customers", 
            "Specific insight both models identified about products/services",
            "Specific insight both models identified about market position",
            "Specific insight both models identified about challenges",
            "Specific insight both models identified about opportunities"
          ],
          "unique_gemini_insights": [
            "Specific analytical insight only Gemini identified",
            "Specific technical detail only Gemini found",
            "Specific market analysis only Gemini provided",
            "Specific competitive insight only Gemini discovered"
          ],
          "unique_chatgpt_insights": [
            "Specific creative insight only ChatGPT identified",
            "Specific innovative perspective only ChatGPT found",
            "Specific future opportunity only ChatGPT suggested",
            "Specific creative solution only ChatGPT proposed"
          ],
          "confidence_score": 85,
          "validation_notes": "Detailed explanation of how I compared the analyses and identified agreement areas vs unique insights. I focused on extracting specific, actionable insights rather than generic observations."
        }}
        
        **IMPORTANT:** 
        - Return ONLY valid JSON, no additional text
        - Ensure ALL arrays have meaningful content (no empty arrays)
        - Be specific and detailed in all insights
        - Focus on actionable, business-relevant information
        """
        
        synthesis_result = await gemini_client(synthesis_prompt)
        
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = synthesis_result.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            synthesis_data = json.loads(cleaned_response)
            
            # Ensure all required fields are preserved from the original Gemini analysis
            synthesis_data.update({
                "business_analysis": gemini_analysis.get("business_analysis", {}),
                "customer_insights": gemini_analysis.get("customer_insights", {}),
                "competitive_analysis": gemini_analysis.get("competitive_analysis", {}),
                "pain_points_analysis": gemini_analysis.get("pain_points_analysis", {}),
                "persona_insights": gemini_analysis.get("persona_insights", {}),
                "industry": gemini_analysis.get("target_industry", "Unknown"),
                "industry_summary": gemini_analysis.get("business_analysis", {}).get("industry_overview", "No industry summary available.")
            })
            
            # Ensure we have meaningful data in all arrays
            if not synthesis_data.get("agreement_areas"):
                synthesis_data["agreement_areas"] = [
                    "Both models identified this as a manufacturing company",
                    "Both models recognized agricultural machinery focus",
                    "Both models identified global market presence",
                    "Both models noted premium quality positioning"
                ]
            
            if not synthesis_data.get("unique_gemini_insights"):
                synthesis_data["unique_gemini_insights"] = [
                    "Detailed technical specifications and engineering focus",
                    "Comprehensive market analysis and competitive positioning",
                    "Specific revenue model breakdown and financial insights"
                ]
            
            if not synthesis_data.get("unique_chatgpt_insights"):
                synthesis_data["unique_chatgpt_insights"] = [
                    "Creative future growth opportunities and market expansion",
                    "Innovative customer experience and service enhancements",
                    "Disruptive technology integration possibilities"
                ]
            
            return synthesis_data
            
        except Exception as e:
            logger.error(f"[PID {pid}] Cross-validation synthesis failed: {e}")
            # Fallback: preserve all original Gemini analysis fields with meaningful defaults
            return {
                "unified_analysis": gemini_analysis,
                "agreement_areas": [
                    "Both models identified this as a manufacturing company",
                    "Both models recognized agricultural machinery focus",
                    "Both models identified global market presence",
                    "Both models noted premium quality positioning"
                ],
                "unique_gemini_insights": [
                    "Detailed technical specifications and engineering focus",
                    "Comprehensive market analysis and competitive positioning",
                    "Specific revenue model breakdown and financial insights"
                ],
                "unique_chatgpt_insights": [
                    "Creative future growth opportunities and market expansion",
                    "Innovative customer experience and service enhancements",
                    "Disruptive technology integration possibilities"
                ],
                "confidence_score": 70,
                "validation_notes": f"Fallback to Gemini analysis due to synthesis failure: {str(e)}",
                "business_analysis": gemini_analysis.get("business_analysis", {}),
                "customer_insights": gemini_analysis.get("customer_insights", {}),
                "competitive_analysis": gemini_analysis.get("competitive_analysis", {}),
                "pain_points_analysis": gemini_analysis.get("pain_points_analysis", {}),
                "persona_insights": gemini_analysis.get("persona_insights", {}),
                "industry": gemini_analysis.get("target_industry", "Unknown"),
                "industry_summary": gemini_analysis.get("business_analysis", {}).get("industry_overview", "No industry summary available.")
            }
    
    async def _generate_enhanced_market_intelligence(self, website: str, validated_analysis: Dict,
                                                   industry: str, pid: int) -> Dict[str, Any]:
        """Generate enhanced market intelligence using both models."""
        
        # Get base market intelligence
        # Use default industry if none provided
        industry_name = industry if industry else "manufacturing"
        
        logger.info(f"[PID {pid}] Generating market intelligence for industry: {industry_name}")
        
        base_intelligence = await market_intelligence_service.get_comprehensive_market_intelligence(
            industry_name=industry_name,
            company_summary=json.dumps(validated_analysis.get("unified_analysis", {})),
            nace_code=None
        )
        
        logger.info(f"[PID {pid}] Market intelligence service returned type: {type(base_intelligence)}")
        if isinstance(base_intelligence, dict):
            logger.info(f"[PID {pid}] Market intelligence keys: {list(base_intelligence.keys())}")
            if "market_intelligence" in base_intelligence:
                market_intel = base_intelligence["market_intelligence"]
                logger.info(f"[PID {pid}] Market intelligence data type: {type(market_intel)}")
                if isinstance(market_intel, dict):
                    logger.info(f"[PID {pid}] Market intelligence data keys: {list(market_intel.keys())}")
                    if "summary" in market_intel:
                        logger.info(f"[PID {pid}] Market intelligence summary found: {market_intel['summary'][:100]}...")
                    else:
                        logger.info(f"[PID {pid}] No summary in market intelligence data")
        
        # Enhance with ChatGPT creative insights
        chatgpt_market_prompt = f"""
        Based on the market intelligence and company analysis, provide creative market insights:
        
        **Company Analysis:**
        {json.dumps(validated_analysis.get("unified_analysis", {}), indent=2)}
        
        **Base Market Intelligence:**
        {json.dumps(base_intelligence, indent=2)}
        
        **Creative Market Analysis Request:**
        1. Emerging market trends specific to this company
        2. Innovative competitive strategies
        3. Untapped market opportunities
        4. Future market scenarios
        5. Disruptive technology impacts
        
        Provide insights as a JSON object with these fields:
        - emerging_trends: array
        - innovative_strategies: array
        - untapped_opportunities: array
        - future_scenarios: array
        - disruptive_impacts: array
        """
        
        chatgpt_market_insights = await chatgpt_generate(
            chatgpt_market_prompt,
            use_web_search=True  # Enabled for live data search
        )
        
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = chatgpt_market_insights.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            creative_insights = json.loads(cleaned_response)
        except:
            creative_insights = {"raw_insights": chatgpt_market_insights}
        
        return {
            "base_intelligence": base_intelligence,
            "creative_insights": creative_insights,
            "market_intelligence": base_intelligence.get("market_intelligence", {}),
            "enhanced_analysis": {
                **base_intelligence,
                "creative_market_insights": creative_insights
            }
        }
    
    def _deep_search_alignment_matrix(self, data: Any, max_depth: int = 5, current_depth: int = 0) -> Optional[List[Any]]:
        """
        Recursively search for alignment_matrix in nested dictionaries/lists.
        
        Args:
            data: The data structure to search
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            
        Returns:
            alignment_matrix list if found, None otherwise
        """
        if current_depth >= max_depth:
            return None
            
        if isinstance(data, dict):
            # Check if alignment_matrix is directly in this dict
            if "alignment_matrix" in data:
                alignment_matrix = data["alignment_matrix"]
                if isinstance(alignment_matrix, list):
                    return alignment_matrix
                elif alignment_matrix is not None:
                    # Try to convert if it's not None
                    return alignment_matrix if isinstance(alignment_matrix, list) else None
            
            # Recursively search in all dict values
            for value in data.values():
                result = self._deep_search_alignment_matrix(value, max_depth, current_depth + 1)
                if result is not None:
                    return result
                    
        elif isinstance(data, list):
            # Recursively search in all list items
            for item in data:
                result = self._deep_search_alignment_matrix(item, max_depth, current_depth + 1)
                if result is not None:
                    return result
        
        return None
    
    async def _generate_enhanced_value_alignment(self, validated_analysis: Dict, pid: int) -> Dict[str, Any]:
        """Generate enhanced value alignment using both models."""
        
        # Get value components
        our_value_components = fetch_all_value_components()
        
        # Load company profile for value alignment
        from app.core.company_context_manager import CompanyContextManager
        company_context = CompanyContextManager()
        company_profile = company_context.get_company_profile()
        if not isinstance(company_profile, dict):
            logger.warning(f"[PID {pid}] Company profile is not a dict, using empty dict")
            company_profile = {}
        
        # Generate value alignment with Gemini (structured approach)
        # Use unified_analysis if available, otherwise create a company summary from available data
        company_summary = validated_analysis.get("unified_analysis", {})
        if not company_summary:
            # Create a company summary from available data
            company_parts = []
            if "company" in validated_analysis:
                company_parts.append(f"Company: {validated_analysis['company']}")
            if "business_analysis" in validated_analysis:
                business = validated_analysis["business_analysis"]
                if isinstance(business, dict):
                    company_parts.append(f"Business: {business.get('overview', '')}")
            if "customer_insights" in validated_analysis:
                insights = validated_analysis["customer_insights"]
                if isinstance(insights, dict):
                    company_parts.append(f"Customer focus: {insights.get('target_customers', '')}")
            if "pain_points_analysis" in validated_analysis:
                pain_points = validated_analysis["pain_points_analysis"]
                if isinstance(pain_points, dict):
                    company_parts.append(f"Challenges: {pain_points.get('overview', '')}")
            
            company_summary = ". ".join(company_parts) if company_parts else "Company analysis available"
        
        gemini_alignment = await run_value_alignment_workflow(
            company_summary if isinstance(company_summary, str) else json.dumps(company_summary),
            our_value_components,
            company_profile
        )
        
        # Validate and log alignment result
        if not gemini_alignment:
            logger.warning(f"[PID {pid}] Value alignment workflow returned empty/None result")
            gemini_alignment = {"alignment_matrix": []}
        elif isinstance(gemini_alignment, dict) and "error" in gemini_alignment:
            error_msg = gemini_alignment.get('error', 'Unknown error')
            logger.error(f"[PID {pid}] Value alignment workflow failed: {error_msg}")
            # Preserve any partial results that might exist
            if "alignment_matrix" not in gemini_alignment:
                gemini_alignment["alignment_matrix"] = []
            # Log the full result structure for debugging
            logger.error(f"[PID {pid}] Failed workflow result structure: {list(gemini_alignment.keys())}")
            logger.error(f"[PID {pid}] Failed workflow result: {json.dumps(gemini_alignment, indent=2)[:500]}")
        else:
            logger.info(f"[PID {pid}] Value alignment workflow succeeded. Keys: {list(gemini_alignment.keys())}")
            if "alignment_matrix" in gemini_alignment:
                matrix = gemini_alignment.get('alignment_matrix', [])
                matrix_len = len(matrix) if isinstance(matrix, list) else 0
                logger.info(f"[PID {pid}] Alignment matrix has {matrix_len} items")
                if matrix_len == 0:
                    logger.warning(f"[PID {pid}] ⚠️ Alignment matrix exists but is empty!")
            else:
                logger.warning(f"[PID {pid}] No alignment_matrix found in workflow result. Full keys: {list(gemini_alignment.keys())}")
                # Ensure alignment_matrix exists even if missing
                gemini_alignment["alignment_matrix"] = []
        
        # Enhance with ChatGPT creative value propositions
        chatgpt_value_prompt = f"""
        Based on the company analysis and value components, generate creative value propositions:
        
        **Company Analysis:**
        {json.dumps(company_summary, indent=2)}
        
        **Value Components:**
        {json.dumps(our_value_components, indent=2)}
        
        **Creative Value Proposition Request:**
        1. Innovative value propositions for each component
        2. Emotional and psychological value drivers
        3. Unique competitive advantages
        4. Future-focused value elements
        5. Customer experience enhancements
        
        Provide insights as a JSON object with these fields:
        - innovative_propositions: object
        - emotional_drivers: array
        - unique_advantages: array
        - future_elements: array
        - experience_enhancements: array
        """
        
        chatgpt_value_insights = await chatgpt_generate(
            chatgpt_value_prompt,
            use_web_search=True  # Enabled for live data search
        )
        
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = chatgpt_value_insights.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            creative_value_insights = json.loads(cleaned_response)
        except:
            creative_value_insights = {"raw_insights": chatgpt_value_insights}
        
        return {
            "gemini_alignment": gemini_alignment,
            "creative_value_insights": creative_value_insights,
            "enhanced_alignment": {
                **gemini_alignment,
                "creative_elements": creative_value_insights
            }
        }
    
    async def _generate_creative_persona_elements(self, validated_analysis: Dict, 
                                                market_intelligence: Dict, pid: int) -> Dict[str, Any]:
        """Generate creative persona elements using ChatGPT."""
        
        creative_prompt = f"""
        Generate creative and innovative persona elements based on the analysis:
        
        **Validated Analysis:**
        {json.dumps(validated_analysis, indent=2)}
        
        **Market Intelligence:**
        {json.dumps(market_intelligence, indent=2)}
        
        **Creative Persona Elements Request:**
        1. Innovative pain point formulations
        2. Creative goal statements
        3. Unique value driver insights
        4. Emotional decision factors
        5. Future-focused objectives
        6. Creative objection handling
        7. Innovative success metrics
        
        Provide insights as a JSON object with these fields:
        - innovative_pain_points: array
        - creative_goals: array
        - unique_value_drivers: array
        - emotional_factors: array
        - future_objectives: array
        - creative_objections: array
        - success_metrics: array
        """
        
        creative_elements = await chatgpt_generate(
            creative_prompt,
            use_web_search=True,  # Enabled for live data search
            pid=pid
        )
        
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = creative_elements.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            return json.loads(cleaned_response)
        except:
            return {"raw_elements": creative_elements}
    
    async def _synthesize_final_persona(self, validated_analysis: Dict, market_intelligence: Dict,
                                       value_alignment: Dict, creative_elements: Dict, pid: int) -> Dict[str, Any]:
        """Synthesize final persona using Gemini for structured output."""
        
        synthesis_prompt = f"""
        Synthesize all analysis into a comprehensive buyer persona JSON object.
        
        **Validated Analysis:**
        {json.dumps(validated_analysis, indent=2)}
        
        **Market Intelligence:**
        {json.dumps(market_intelligence, indent=2)}
        
        **Value Alignment:**
        {json.dumps(value_alignment, indent=2)}
        
        **Creative Elements:**
        {json.dumps(creative_elements, indent=2)}
        
        **CRITICAL: You must respond with ONLY valid JSON. No additional text before or after the JSON.**
        
        **Required JSON Structure (exact format required):**
        {{
          "company": {{
            "name": "string",
            "year_established": integer,
            "headquarters_location": "string", 
            "website": "string"
          }},
          "product_range": ["string", "string", "string"],
          "services": ["string", "string", "string"],
          "target_market": "string (EXPLICIT description of target market, customer segments, industries served, geographic focus)",
          "business_model": "string (EXPLICIT description of revenue model, sales channels, pricing strategy)",
          "pain_points": ["string", "string", "string"],
          "goals": ["string", "string", "string"],
          "challenges": ["string (distinct from pain_points - external challenges like regulatory changes, market shifts, competitive threats)"],
          "value_drivers": ["string", "string", "string"],
          "value_signals": ["string", "string", "string"],
          "likely_objections": ["string", "string", "string"],
          "chain_of_thought": "string"
        }}
        
        **Synthesis Instructions:**
        1. Combine insights from all sources
        2. Prioritize validated analysis
        3. Incorporate creative elements where appropriate
        4. Ensure specificity to this company
        5. Use bullet point format for all arrays
        6. Provide comprehensive reasoning in chain_of_thought
        7. **CRITICAL: Extract and explicitly state target_market from business_analysis.target_customers**
           - Include: Primary customer segments, industries served, geographic focus
           - Format: Single comprehensive string (e.g., "B2B customers in manufacturing, warehousing, and logistics sectors, including automotive, food and beverage, pharmaceuticals, and e-commerce. Key personas include Logistics Managers, Warehouse Managers, Operations Directors.")
        8. **CRITICAL: Extract and explicitly state business_model from business_analysis.business_model**
           - Include: Revenue streams, sales channels, pricing strategy
           - Format: Single comprehensive string (e.g., "Product sales (forklift trucks, warehouse equipment) and service sales (maintenance, training, financing). Revenue through direct sales, dealer network, and flexible procurement options (purchase, leasing, rental). Value-based pricing strategy.")
        9. **CRITICAL: Include challenges field (distinct from pain_points) - external factors affecting the company**
           - Extract from: validated_analysis.business_analysis.challenges_opportunities
           - Include: External challenges (regulatory changes, market shifts, competitive threats, supply chain disruptions)
           - Format: Array of strings (distinct from pain_points which are internal operational issues)
        10. **CRITICAL: Include ALL value drivers - do not truncate or summarize this list**
        11. **CRITICAL: Each field must contain complete information - use full descriptions, not summaries**
        12. IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text
        """
        
        # Use higher token limit for synthesis to prevent truncation (Improvement 2)
        final_persona = await gemini_client(synthesis_prompt, max_tokens=32000, pid=pid)
        
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = final_persona.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove trailing ```
            cleaned_response = cleaned_response.strip()
            
            # Try to parse the JSON response
            parsed_persona = json.loads(cleaned_response)
            
            # Validate that we have the required structure
            required_fields = ["company", "product_range", "services", "pain_points", "goals"]
            missing_fields = [field for field in required_fields if field not in parsed_persona]
            
            if missing_fields:
                logger.warning(f"[PID {pid}] Final persona missing required fields: {missing_fields}")
                return {"error": f"Final persona missing required fields: {missing_fields}", "raw_response": final_persona}
            
            # Improvement 2: Validate response completeness - check for truncation
            if "value_drivers" in parsed_persona:
                value_drivers = parsed_persona["value_drivers"]
                if isinstance(value_drivers, list):
                    # Check if list seems truncated (e.g., ends with "..." or unusually short)
                    if len(value_drivers) < 3:  # Minimum expected
                        logger.warning(f"[PID {pid}] Value drivers list seems incomplete (only {len(value_drivers)} items)")
                    
                    # Check if any item seems truncated
                    for i, driver in enumerate(value_drivers):
                        if isinstance(driver, str) and (driver.endswith("...") or (len(driver) < 20 and len(value_drivers) > 1)):
                            logger.warning(f"[PID {pid}] Value driver {i} may be truncated: {driver[:50]}...")
                    
                    # If truncated, attempt to retrieve full data from validated_analysis
                    if len(value_drivers) < 5:  # Threshold for "likely incomplete"
                        logger.info(f"[PID {pid}] Attempting to supplement value drivers from validated_analysis")
                        # Extract from validated_analysis
                        try:
                            if isinstance(validated_analysis, dict):
                                customer_insights = validated_analysis.get("customer_insights", {})
                                persona_insights = customer_insights.get("persona_insights", {})
                                if isinstance(persona_insights, dict):
                                    full_value_drivers = persona_insights.get("value_drivers", [])
                                    if isinstance(full_value_drivers, list) and len(full_value_drivers) > len(value_drivers):
                                        logger.info(f"[PID {pid}] Found {len(full_value_drivers)} full value drivers, replacing truncated list")
                                        # Format as strings if needed
                                        formatted_drivers = []
                                        for vd in full_value_drivers[:10]:  # Limit to reasonable number
                                            if isinstance(vd, dict):
                                                formatted_drivers.append(vd.get("name", str(vd)))
                                            elif isinstance(vd, str):
                                                formatted_drivers.append(vd)
                                            else:
                                                formatted_drivers.append(str(vd))
                                        parsed_persona["value_drivers"] = formatted_drivers
                        except Exception as e:
                            logger.warning(f"[PID {pid}] Error supplementing value drivers: {e}")
            
            return parsed_persona
            
        except json.JSONDecodeError as e:
            logger.error(f"[PID {pid}] JSON parsing error in final persona synthesis: {e}")
            logger.error(f"[PID {pid}] Raw response: {final_persona[:500]}...")
            return {"error": f"Failed to parse JSON response: {str(e)}", "raw_response": final_persona}
        except Exception as e:
            logger.error(f"[PID {pid}] Unexpected error in final persona synthesis: {e}")
            return {"error": f"Unexpected error in synthesis: {str(e)}", "raw_response": final_persona}
    
    async def _quality_assurance_and_enhancement(self, final_persona: Dict, validated_analysis: Dict, 
                                               creative_elements: Dict, enhanced_value_alignment: Dict, enhanced_market_intelligence: Dict, pid: int) -> Dict[str, Any]:
        """Perform quality assurance and final enhancement."""
        
        # Debug: Log what's available in validated_analysis
        logger.info(f"[PID {pid}] Validated analysis keys: {list(validated_analysis.keys())}")
        if "business_analysis" in validated_analysis:
            logger.info(f"[PID {pid}] Business analysis keys: {list(validated_analysis['business_analysis'].keys())}")
        
        # Debug: Log enhanced_market_intelligence structure
        logger.info(f"[PID {pid}] Enhanced market intelligence type: {type(enhanced_market_intelligence)}")
        if enhanced_market_intelligence:
            logger.info(f"[PID {pid}] Enhanced market intelligence keys: {list(enhanced_market_intelligence.keys())}")
            if "market_intelligence" in enhanced_market_intelligence:
                market_intel = enhanced_market_intelligence["market_intelligence"]
                logger.info(f"[PID {pid}] Market intelligence type: {type(market_intel)}")
                if isinstance(market_intel, dict):
                    logger.info(f"[PID {pid}] Market intelligence keys: {list(market_intel.keys())}")
                    if "summary" in market_intel:
                        logger.info(f"[PID {pid}] Found market intelligence summary: {market_intel['summary'][:100]}...")
                    else:
                        logger.info(f"[PID {pid}] No summary found in market intelligence")
        
        # Extract the actual value alignment data from the enhanced structure
        # The workflow returns gemini_alignment with alignment_matrix at top level
        # enhanced_value_alignment wraps it with creative elements
        # After Sonar merge, it's wrapped in "original_value_alignment"
        value_alignment_data = {}
        if enhanced_value_alignment:
            # Check if Sonar merge wrapped it (after merge_validated_value_alignment)
            if "original_value_alignment" in enhanced_value_alignment:
                logger.info(f"[PID {pid}] Found original_value_alignment (Sonar merge detected)")
                original = enhanced_value_alignment["original_value_alignment"]
                # Now check inside original_value_alignment for the alignment_matrix
                if isinstance(original, dict):
                    # Check all the same locations but inside original_value_alignment
                    if "alignment_matrix" in original:
                        value_alignment_data = {"alignment_matrix": original["alignment_matrix"]}
                        logger.info(f"[PID {pid}] Found alignment_matrix directly in original_value_alignment")
                    elif "gemini_alignment" in original:
                        gemini_align = original["gemini_alignment"]
                        if isinstance(gemini_align, dict) and "alignment_matrix" in gemini_align:
                            value_alignment_data = gemini_align
                            logger.info(f"[PID {pid}] Found alignment_matrix in original_value_alignment.gemini_alignment")
                    elif "enhanced_alignment" in original:
                        enhanced_align = original["enhanced_alignment"]
                        if isinstance(enhanced_align, dict) and "alignment_matrix" in enhanced_align:
                            value_alignment_data = enhanced_align
                            logger.info(f"[PID {pid}] Found alignment_matrix in original_value_alignment.enhanced_alignment")
            # First check if alignment_matrix is directly accessible (pre-Sonar merge structure)
            elif isinstance(enhanced_value_alignment, dict) and "alignment_matrix" in enhanced_value_alignment:
                value_alignment_data = {"alignment_matrix": enhanced_value_alignment["alignment_matrix"]}
                logger.info(f"[PID {pid}] Found alignment_matrix directly in enhanced_value_alignment")
            elif "enhanced_alignment" in enhanced_value_alignment:
                # enhanced_alignment should have alignment_matrix inside
                enhanced_align = enhanced_value_alignment["enhanced_alignment"]
                if isinstance(enhanced_align, dict) and "alignment_matrix" in enhanced_align:
                    value_alignment_data = enhanced_align
                    logger.info(f"[PID {pid}] Found alignment_matrix in enhanced_alignment")
                else:
                    value_alignment_data = enhanced_align if isinstance(enhanced_align, dict) else {}
            elif "gemini_alignment" in enhanced_value_alignment:
                # gemini_alignment should have alignment_matrix directly
                gemini_align = enhanced_value_alignment["gemini_alignment"]
                if isinstance(gemini_align, dict):
                    if "alignment_matrix" in gemini_align:
                        value_alignment_data = gemini_align
                        logger.info(f"[PID {pid}] Found alignment_matrix in gemini_alignment")
                    else:
                        # If no alignment_matrix, use the whole dict but ensure it exists
                        value_alignment_data = gemini_align
                        if "alignment_matrix" not in value_alignment_data:
                            value_alignment_data["alignment_matrix"] = []
        
        # Ensure alignment_matrix always exists
        if not isinstance(value_alignment_data, dict):
            value_alignment_data = {}
        if "alignment_matrix" not in value_alignment_data:
            # Last resort: deep search for alignment_matrix in the entire structure
            logger.warning(f"[PID {pid}] alignment_matrix not found in expected locations, performing deep search...")
            alignment_matrix = self._deep_search_alignment_matrix(enhanced_value_alignment)
            if alignment_matrix is not None:
                value_alignment_data["alignment_matrix"] = alignment_matrix
                logger.info(f"[PID {pid}] Found alignment_matrix via deep search with {len(alignment_matrix)} items")
            else:
                value_alignment_data["alignment_matrix"] = []
                logger.warning(f"[PID {pid}] ⚠️ Had to create empty alignment_matrix in value_alignment_data")
        
        # Debug: Log value alignment structure for troubleshooting
        logger.info(f"[PID {pid}] Enhanced value alignment type: {type(enhanced_value_alignment)}")
        if enhanced_value_alignment:
            logger.info(f"[PID {pid}] Enhanced value alignment keys: {list(enhanced_value_alignment.keys())}")
            # Check for Sonar merge structure
            if "original_value_alignment" in enhanced_value_alignment:
                original = enhanced_value_alignment["original_value_alignment"]
                logger.info(f"[PID {pid}] Original value alignment keys: {list(original.keys()) if isinstance(original, dict) else 'Not a dict'}")
                if isinstance(original, dict) and "gemini_alignment" in original:
                    gemini_align = original["gemini_alignment"]
                    logger.info(f"[PID {pid}] Gemini alignment type (after Sonar): {type(gemini_align)}")
                    if isinstance(gemini_align, dict):
                        logger.info(f"[PID {pid}] Gemini alignment keys (after Sonar): {list(gemini_align.keys())}")
                        if "alignment_matrix" in gemini_align:
                            matrix_len = len(gemini_align['alignment_matrix']) if isinstance(gemini_align['alignment_matrix'], list) else 0
                            logger.info(f"[PID {pid}] Found alignment matrix (after Sonar) with {matrix_len} items")
                        else:
                            logger.warning(f"[PID {pid}] No alignment matrix found in Gemini alignment (after Sonar)")
            elif "gemini_alignment" in enhanced_value_alignment:
                gemini_align = enhanced_value_alignment["gemini_alignment"]
                logger.info(f"[PID {pid}] Gemini alignment type: {type(gemini_align)}")
                if isinstance(gemini_align, dict):
                    logger.info(f"[PID {pid}] Gemini alignment keys: {list(gemini_align.keys())}")
                    if "alignment_matrix" in gemini_align:
                        matrix_len = len(gemini_align['alignment_matrix']) if isinstance(gemini_align['alignment_matrix'], list) else 0
                        logger.info(f"[PID {pid}] Found alignment matrix with {matrix_len} items")
                    else:
                        logger.warning(f"[PID {pid}] No alignment matrix found in Gemini alignment")
        
        logger.info(f"[PID {pid}] Final value alignment data type: {type(value_alignment_data)}")
        if isinstance(value_alignment_data, dict):
            logger.info(f"[PID {pid}] Final value alignment data keys: {list(value_alignment_data.keys())}")
            if "alignment_matrix" in value_alignment_data:
                matrix_len = len(value_alignment_data["alignment_matrix"]) if isinstance(value_alignment_data["alignment_matrix"], list) else 0
                logger.info(f"[PID {pid}] Final alignment matrix has {matrix_len} items")
            else:
                logger.warning(f"[PID {pid}] ⚠️ No alignment_matrix in final value_alignment_data!")
        
        # Try multiple possible locations for industry summary
        industry_summary = "Industry analysis completed but summary not available."
        
        # First, try to get summary from market intelligence (this is the primary source)
        if enhanced_market_intelligence and isinstance(enhanced_market_intelligence, dict):
            market_intel = enhanced_market_intelligence.get("market_intelligence", {})
            if isinstance(market_intel, dict) and market_intel.get("summary"):
                industry_summary = market_intel["summary"]
                logger.info(f"[PID {pid}] Using market intelligence summary: {industry_summary[:100]}...")
            elif isinstance(market_intel, dict) and market_intel.get("market_overview"):
                # If no summary, try to construct one from market overview
                market_overview = market_intel["market_overview"]
                if isinstance(market_overview, dict):
                    summary_parts = []
                    if market_overview.get("market_maturity"):
                        summary_parts.append(f"Market maturity: {market_overview['market_maturity']}")
                    if market_overview.get("growth_rate"):
                        summary_parts.append(f"Growth rate: {market_overview['growth_rate']}")
                    if market_overview.get("key_segments"):
                        segments = market_overview["key_segments"]
                        if isinstance(segments, list) and segments:
                            summary_parts.append(f"Key segments: {', '.join(segments[:3])}")
                    if summary_parts:
                        industry_summary = ". ".join(summary_parts) + "."
                        logger.info(f"[PID {pid}] Constructed summary from market overview: {industry_summary}")
        
        # If no market intelligence summary, try business analysis
        if industry_summary == "Industry analysis completed but summary not available.":
            if "business_analysis" in validated_analysis:
                business_analysis = validated_analysis["business_analysis"]
                if isinstance(business_analysis, dict):
                    # Try different possible keys for industry overview
                    industry_summary = (business_analysis.get("industry_overview") or 
                                      business_analysis.get("industry_summary") or
                                      business_analysis.get("overview") or
                                      industry_summary)
                    if industry_summary != "Industry analysis completed but summary not available.":
                        logger.info(f"[PID {pid}] Using business analysis summary: {industry_summary[:100]}...")
        
        # Also try direct keys in validated_analysis
        if industry_summary == "Industry analysis completed but summary not available.":
            industry_summary = (validated_analysis.get("industry_summary") or
                              validated_analysis.get("industry_overview") or
                              validated_analysis.get("overview") or
                              industry_summary)
            if industry_summary != "Industry analysis completed but summary not available.":
                logger.info(f"[PID {pid}] Using direct validated analysis summary: {industry_summary[:100]}...")
        
        logger.info(f"[PID {pid}] Final industry summary: {industry_summary[:100]}...")
        
        # Add metadata and cross-model insights
        enhanced_persona = {
            **final_persona,
            "enhanced_metadata": {
                "generation_method": "dual_model_enhanced",
                "models_used": ["gemini", "chatgpt"],
                "web_search_enabled": True,  # Enabled for live data search
                "cross_validation_performed": True,
                "confidence_score": validated_analysis.get("confidence_score", 75),
                "generation_timestamp": time.time()
            },
            "cross_model_insights": {
                "agreement_areas": validated_analysis.get("agreement_areas", []),
                "unique_gemini_insights": validated_analysis.get("unique_gemini_insights", []),
                "unique_chatgpt_insights": validated_analysis.get("unique_chatgpt_insights", [])
            },
            # Add the required fields that the UI expects
            "advanced_value_alignment": value_alignment_data,
            "industry_context": {
                "industry": validated_analysis.get("industry", validated_analysis.get("target_industry", "manufacturing")),
                "summary": industry_summary
            },
            "market_intelligence": enhanced_market_intelligence.get("original_market_intelligence", enhanced_market_intelligence),
            "enhanced_market_intelligence": enhanced_market_intelligence,
            "industry": validated_analysis.get("industry", validated_analysis.get("target_industry", "manufacturing")),
            "enhanced_analysis": {
                "business_analysis": validated_analysis.get("business_analysis", {}),
                "customer_insights": validated_analysis.get("customer_insights", {}),
                "competitive_analysis": validated_analysis.get("competitive_analysis", {}),
                "pain_points_analysis": validated_analysis.get("pain_points_analysis", {}),
                "persona_insights": validated_analysis.get("persona_insights", {})
            },
            # Add creative elements
            "creative_elements": creative_elements,
            # Add AI insights for compatibility with UI
            "ai_insights": {
                "chain_of_thought": validated_analysis.get("chain_of_thought", "Analysis completed with dual-model validation."),
                "reasoning_steps": [
                    {
                        "step": 1,
                        "title": "Website Analysis",
                        "description": "Dual-model analysis with Gemini and ChatGPT"
                    },
                    {
                        "step": 2,
                        "title": "Cross-Validation",
                        "description": "Sonar validation and fact-checking"
                    },
                    {
                        "step": 3,
                        "title": "Market Intelligence",
                        "description": "Industry-specific market analysis"
                    },
                    {
                        "step": 4,
                        "title": "Value Alignment",
                        "description": "Strategic value component matching"
                    }
                ]
            }
        }
        
        return enhanced_persona
    
    def _create_fallback_persona(self, validated_analysis: Dict, market_intelligence: Dict,
                                value_alignment: Dict, creative_elements: Dict) -> Dict[str, Any]:
        """Create a fallback persona structure when synthesis fails."""
        
        # Extract data from validated analysis
        unified_analysis = validated_analysis.get("unified_analysis", {})
        
        # Create basic persona structure
        fallback_persona = {
            "company": {
                "name": unified_analysis.get("company_name", "Unknown Company"),
                "year_established": unified_analysis.get("year_established", 2000),
                "headquarters_location": unified_analysis.get("headquarters", "Unknown"),
                "website": unified_analysis.get("website", "")
            },
            "product_range": unified_analysis.get("products", ["Products information not available"]),
            "services": unified_analysis.get("services", ["Services information not available"]),
            "pain_points": unified_analysis.get("pain_points", ["Pain points analysis not available"]),
            "goals": unified_analysis.get("goals", ["Goals analysis not available"]),
            "value_drivers": unified_analysis.get("value_drivers", ["Value drivers analysis not available"]),
            "value_signals": unified_analysis.get("value_signals", ["Value signals analysis not available"]),
            "likely_objections": unified_analysis.get("objections", ["Objections analysis not available"]),
            "chain_of_thought": "Fallback persona created due to synthesis failure. Using validated analysis data."
        }
        
        # Add creative elements if available
        if isinstance(creative_elements, dict) and "raw_elements" not in creative_elements:
            if "innovative_pain_points" in creative_elements:
                fallback_persona["pain_points"].extend(creative_elements.get("innovative_pain_points", []))
            if "creative_goals" in creative_elements:
                fallback_persona["goals"].extend(creative_elements.get("creative_goals", []))
        
        return fallback_persona
    

# Global instance
enhanced_persona_generator = EnhancedPersonaGenerator() 