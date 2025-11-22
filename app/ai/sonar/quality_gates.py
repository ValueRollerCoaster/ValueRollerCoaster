"""
Quality Gates
Controls the persona generation process flow with validation checkpoints.
"""

import logging
from typing import Dict, List, Any, Optional
from .sonar_client import sonar_client
from .relevance_validator import RelevanceValidator
from .domain_validator import DomainValidator

logger = logging.getLogger(__name__)

class QualityGates:
    """Quality gate system for persona generation process control"""
    
    def __init__(self):
        self.relevance_validator = RelevanceValidator()
        self.domain_validator = DomainValidator()
        logger.info("[QualityGates] Initialized with validators")
    
    async def step_0_relevance_validation(self, website_url: str, website_content: Optional[str] = None, pid: int = 0) -> Dict[str, Any]:
        """
        Step 0: Pre-analysis relevance validation.
        
        Args:
            website_url: Target website URL
            website_content: Optional website content
            pid: Process ID for logging
            
        Returns:
            Relevance validation result with action recommendation
        """
        logger.info(f"[PID {pid}] [QualityGates] Step 0: Relevance validation for: {website_url}")
        
        try:
            # Check if Sonar is available
            if not await sonar_client.is_available():
                logger.warning(f"[PID {pid}] [QualityGates] Sonar not available, skipping relevance validation")
                return {
                    "is_relevant": True,  # Default to proceed if Sonar unavailable
                    "relevance_score": 5,
                    "recommended_action": "proceed",
                    "sonar_available": False
                }
            
            # Perform relevance validation
            relevance_result = await self.relevance_validator.validate_website_relevance(
                website_url, website_content, pid
            )
            
            # Add quality gate metadata
            relevance_result["quality_gate"] = "step_0_relevance"
            relevance_result["sonar_available"] = True
            
            logger.info(f"[PID {pid}] [QualityGates] Step 0 complete - Action: {relevance_result.get('recommended_action', 'unknown')}")
            return relevance_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [QualityGates] Step 0 error: {e}")
            return {
                "is_relevant": False,
                "relevance_score": 0,
                "recommended_action": "skip",
                "error": f"Step 0 validation failed: {str(e)}",
                "quality_gate": "step_0_relevance"
            }
    
    async def step_1_customer_focus_validation(self, analysis: Dict, website_url: str, pid: int = 0) -> Dict[str, Any]:
        """
        Step 1: Customer focus validation after initial analysis.
        
        Args:
            analysis: Current analysis to validate
            website_url: Website URL for context
            pid: Process ID for logging
            
        Returns:
            Customer focus validation result
        """
        logger.info(f"[PID {pid}] [QualityGates] Step 1: Customer focus validation for: {website_url}")
        
        try:
            # Check if Sonar is available
            if not await sonar_client.is_available():
                logger.warning(f"[PID {pid}] [QualityGates] Sonar not available, skipping customer focus validation")
                return {
                    "customer_focus_correct": True,
                    "confidence_score": 5,
                    "should_proceed": True,
                    "sonar_available": False
                }
            
            # Perform customer focus validation
            focus_result = await self.domain_validator.prevent_misinterpretations(analysis, website_url, pid)
            
            # Determine if should proceed
            should_proceed = focus_result.get("interpretation_correct", False)
            confidence_score = focus_result.get("confidence_score", 0)
            
            result = {
                "customer_focus_correct": focus_result.get("interpretation_correct", False),
                "confidence_score": confidence_score,
                "should_proceed": should_proceed,
                "actual_company": focus_result.get("actual_company", "Unknown"),
                "misinterpretation_detected": focus_result.get("misinterpretation_detected", ""),
                "correction_needed": focus_result.get("correction_needed", ""),
                "quality_gate": "step_1_customer_focus",
                "sonar_available": True
            }
            
            logger.info(f"[PID {pid}] [QualityGates] Step 1 complete - Should proceed: {should_proceed}")
            return result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [QualityGates] Step 1 error: {e}")
            return {
                "customer_focus_correct": False,
                "confidence_score": 0,
                "should_proceed": False,
                "error": f"Step 1 validation failed: {str(e)}",
                "quality_gate": "step_1_customer_focus"
            }
    
    async def step_2_cross_model_validation(self, gemini_analysis: Dict, chatgpt_analysis: Dict, 
                                           website_url: str, pid: int = 0) -> Dict[str, Any]:
        """
        Step 2: Cross-model validation with industry-specific sources.
        
        Args:
            gemini_analysis: Gemini analysis result
            chatgpt_analysis: ChatGPT analysis result
            website_url: Website URL for context
            pid: Process ID for logging
            
        Returns:
            Cross-model validation result
        """
        logger.info(f"[PID {pid}] [QualityGates] Step 2: Cross-model validation for: {website_url}")
        
        try:
            # Check if Sonar is available
            if not await sonar_client.is_available():
                logger.warning(f"[PID {pid}] [QualityGates] Sonar not available, skipping cross-model validation")
                return {
                    "models_agree": True,
                    "confidence_score": 5,
                    "should_proceed": True,
                    "sonar_available": False
                }
            
            # Get target domain and industry context for Sonar
            target_domain = self._extract_domain_from_url(website_url)
            industry_context = self._get_industry_context_for_sonar(gemini_analysis, chatgpt_analysis)
            
            logger.info(f"[PID {pid}] [QualityGates] Target domain: {target_domain}")
            logger.info(f"[PID {pid}] [QualityGates] Industry context: {industry_context[:100]}...")
            
            # Perform cross-model validation with dynamic source discovery
            validation_result = await self._cross_validate_models(
                gemini_analysis, chatgpt_analysis, website_url, target_domain, industry_context, pid
            )
            
            # Add quality gate metadata
            validation_result["quality_gate"] = "step_2_cross_model"
            validation_result["sonar_available"] = True
            validation_result["search_domains"] = [target_domain] if target_domain else []
            
            logger.info(f"[PID {pid}] [QualityGates] Step 2 complete - Models agree: {validation_result.get('models_agree', False)}")
            return validation_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [QualityGates] Step 2 error: {e}")
            return {
                "models_agree": False,
                "confidence_score": 0,
                "should_proceed": False,
                "error": f"Step 2 validation failed: {str(e)}",
                "quality_gate": "step_2_cross_model"
            }
    
    async def _cross_validate_models(self, gemini_analysis: Dict, chatgpt_analysis: Dict, 
                                    website_url: str, target_domain: str, industry_context: str, pid: int = 0) -> Dict[str, Any]:
        """Cross-validate Gemini and ChatGPT analyses with dynamic source discovery"""
        
        # Build enhanced prompt with industry context
        prompt = f"""
        CROSS-MODEL VALIDATION: {website_url}
        
        INDUSTRY CONTEXT: {industry_context}
        
        TASK: Compare and validate analyses from two AI models to ensure consistency.
        Use web search to find authoritative sources about this company and industry.
        
        GEMINI ANALYSIS:
        {str(gemini_analysis)[:1000]}
        
        CHATGPT ANALYSIS:
        {str(chatgpt_analysis)[:1000]}
        
        VALIDATION CRITERIA:
        1. **Customer Focus**: Do both models analyze the same company?
        2. **Business Understanding**: Do both models understand the business correctly?
        3. **Industry Classification**: Do both models classify the industry similarly?
        4. **Product/Service Analysis**: Do both models identify similar products/services?
        5. **Target Market**: Do both models identify similar target markets?
        
        SEARCH INSTRUCTIONS:
        - Search for information about {target_domain} specifically
        - Find industry reports and market analysis related to the detected industry
        - Look for recent news and developments about this company
        - Verify claims made by both AI models against authoritative sources
        
        Return JSON with:
        {{
            "models_agree": true/false,
            "agreement_score": 1-10,
            "key_agreements": ["agreement1", "agreement2"],
            "key_disagreements": ["disagreement1", "disagreement2"],
            "recommended_synthesis": "How to combine the analyses",
            "confidence_score": 1-10,
            "should_proceed": true/false,
            "validation_notes": "Notes about the validation process"
        }}
        """
        
        # Use Sonar with target domain filtering and dynamic source discovery
        search_domains = [target_domain] if target_domain else []
        
        response = await sonar_client.generate_response(
            prompt=prompt,
            search_domain_filter=search_domains,  # Only target domain to prevent hallucination
            pid=pid
        )
        
        result = self._parse_json_response(response, pid)
        result["target_domain"] = target_domain
        result["industry_context"] = industry_context
        result["search_filtered"] = bool(search_domains)
        
        return result
    
    async def final_quality_check(self, final_persona: Dict, website_url: str, pid: int = 0) -> Dict[str, Any]:
        """
        Final quality check before returning persona.
        
        Args:
            final_persona: Final persona to validate
            website_url: Website URL for context
            pid: Process ID for logging
            
        Returns:
            Final quality check result
        """
        logger.info(f"[PID {pid}] [QualityGates] Final quality check for: {website_url}")
        
        try:
            # Check if Sonar is available
            if not await sonar_client.is_available():
                logger.warning(f"[PID {pid}] [QualityGates] Sonar not available, skipping final quality check")
                return {
                    "quality_passed": True,
                    "confidence_score": 5,
                    "should_proceed": True,
                    "sonar_available": False
                }
            
            # Perform final quality check
            quality_result = await self._perform_final_quality_check(final_persona, website_url, pid)
            
            # Add quality gate metadata
            quality_result["quality_gate"] = "final_quality_check"
            quality_result["sonar_available"] = True
            
            logger.info(f"[PID {pid}] [QualityGates] Final quality check complete - Passed: {quality_result.get('quality_passed', False)}")
            return quality_result
            
        except Exception as e:
            logger.error(f"[PID {pid}] [QualityGates] Final quality check error: {e}")
            return {
                "quality_passed": False,
                "confidence_score": 0,
                "should_proceed": False,
                "error": f"Final quality check failed: {str(e)}",
                "quality_gate": "final_quality_check"
            }
    
    async def _perform_final_quality_check(self, final_persona: Dict, website_url: str, pid: int = 0) -> Dict[str, Any]:
        """Perform final quality check on persona"""
        
        prompt = f"""
        FINAL QUALITY CHECK: {website_url}
        
        TASK: Validate the final persona for completeness, accuracy, and relevance.
        
        FINAL PERSONA:
        {str(final_persona)[:1500]}
        
        QUALITY CRITERIA:
        1. **Completeness**: Are all required fields present?
        2. **Accuracy**: Does information match the website?
        3. **Relevance**: Is this relevant to our business?
        4. **Consistency**: Is the information logically consistent?
        5. **Customer Focus**: Is the correct company being analyzed?
        
        Return JSON with:
        {{
            "quality_passed": true/false,
            "completeness_score": 1-10,
            "accuracy_score": 1-10,
            "relevance_score": 1-10,
            "consistency_score": 1-10,
            "overall_confidence": 1-10,
            "issues_found": ["issue1", "issue2"],
            "recommendations": ["recommendation1", "recommendation2"],
            "should_proceed": true/false
        }}
        """
        
        response = await sonar_client.generate_response(prompt, pid=pid)
        return self._parse_json_response(response, pid)
    
    def _parse_json_response(self, response: str, pid: int) -> Dict[str, Any]:
        """Parse JSON response from Sonar"""
        
        if response.startswith("ERROR"):
            logger.error(f"[PID {pid}] [QualityGates] Sonar response error: {response}")
            return {"error": response}
        
        try:
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                logger.warning(f"[PID {pid}] [QualityGates] No JSON found in response: {response}")
                return {"error": "Could not parse Sonar response"}
                
        except json.JSONDecodeError as e:
            logger.error(f"[PID {pid}] [QualityGates] JSON parse error: {e}")
            return {"error": f"JSON parse error: {str(e)}"}
    
    async def is_sonar_available(self) -> bool:
        """Check if Sonar is available for quality gates"""
        return await sonar_client.is_available() 

    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL for search filtering"""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception as e:
            logger.warning(f"[QualityGates] Could not extract domain from {url}: {e}")
            return ""
    
    def _get_industry_context_for_sonar(self, gemini_analysis: Dict, chatgpt_analysis: Dict) -> str:
        """Extract industry context to help Sonar find relevant sources dynamically"""
        
        # Extract industry information from analyses
        detected_industries = set()
        industry_context = []
        
        # Check Gemini analysis
        if gemini_analysis:
            business_analysis = gemini_analysis.get("business_analysis", {})
            industry_overview = business_analysis.get("industry_overview", "")
            target_industry = gemini_analysis.get("target_industry", "")
            
            if industry_overview:
                industry_context.append(f"Industry Overview: {industry_overview}")
            if target_industry:
                industry_context.append(f"Target Industry: {target_industry}")
        
        # Check ChatGPT analysis
        if chatgpt_analysis:
            chatgpt_text = str(chatgpt_analysis)
            # Extract key industry-related information
            if "industry" in chatgpt_text.lower() or "sector" in chatgpt_text.lower():
                # Take first 200 characters that mention industry
                lines = chatgpt_text.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in ["industry", "sector", "market", "business"]):
                        industry_context.append(f"Analysis Context: {line.strip()}")
                        break
        
        # Combine context for Sonar
        combined_context = " | ".join(industry_context) if industry_context else ""
        
        logger.info(f"[QualityGates] Industry context for Sonar: {combined_context[:100]}...")
        
        return combined_context 