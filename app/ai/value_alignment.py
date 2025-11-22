import asyncio
import json
import logging
import os
from typing import Optional
from app.ai.chatgpt_client import chatgpt_generate
import app.utils as utils
from app.ai.prompts import PROMPT_TEMPLATES

# Setup value alignment logger directly
def setup_value_alignment_logger():
    """Sets up a dedicated logger for the value alignment process."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logger = logging.getLogger('value_alignment')
    logger.setLevel(logging.INFO)
    
    # Prevent logs from propagating to the root logger
    logger.propagate = False
    
    # If handlers are already present, do nothing
    if logger.handlers:
        return logger
        
    # File handler
    log_file = os.path.join(log_dir, 'value_alignment.log')
    handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to the logger
    logger.addHandler(handler)
    
    return logger

value_alignment_logger = setup_value_alignment_logger()
from logging import getLogger
import re
from app.ai.gemini_prompts import value_alignment_matrix_prompt
from app.core.company_context_manager import CompanyContextManager

# Get a logger instance
agent_logger = getLogger("value_alignment")

# All value alignment agents now use ChatGPT for LLM calls (switched from Gemini for better reliability)

async def _run_profiler_agent(company_summary: str) -> Optional[dict]:
    """Agent 1: Analyzes the company summary to extract high-level strategic insights."""
    agent_logger.info(f"[DEBUG] Profiler input company_summary: {company_summary}")
    prompt = f"""
    You are a Company Profiler. Analyze the following business summary and extract key strategic insights.
    
    **Business Summary:**
    {company_summary}

    **Your Task:**
    Produce a JSON object with the following fields:
    - `key_goals`: A list of the company's most important stated or implied goals.
    - `implicit_challenges`: A list of challenges the company is likely facing, based on the text.
    - `overall_sentiment`: A single phrase describing the company's strategic focus (e.g., "Cost-Cutting & Efficiency", "Innovation & Market Expansion").

    **JSON Output:**
    """
    value_alignment_logger.info("Running Profiler Agent...")
    response_str = await chatgpt_generate(prompt, temperature=0.2, max_tokens=16384)
    agent_logger.info(f"[DEBUG] Profiler raw ChatGPT response: {response_str}")
    
    # Check if chatgpt_generate returned an error
    if isinstance(response_str, str) and response_str.startswith("ERROR:"):
        error_msg = response_str.replace("ERROR:", "").strip()
        value_alignment_logger.error(f"Profiler agent: ChatGPT client error: {error_msg if error_msg else 'Unknown error (empty message)'}")
        value_alignment_logger.error(f"Profiler agent: Full error response: {repr(response_str)}")
        agent_logger.error(f"[ERROR] Profiler agent: ChatGPT client error: {error_msg if error_msg else 'Unknown error (empty message)'}")
        agent_logger.error(f"[ERROR] Profiler agent: Full error response: {repr(response_str)}")
        return {"error": f"ChatGPT client error: {error_msg if error_msg else 'Unknown error (empty message)'}"}
    
    try:
        # Try to extract JSON from ```json ... ``` code block
        match = re.search(r'```json\s*(\{.*?\})\s*```', response_str, re.DOTALL)
        if not match:
            # Fallback: Try to extract JSON from generic code block ``` ... ```
            match = re.search(r'```\s*(\{.*?\})\s*```', response_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            agent_logger.info("Extracted JSON from markdown block in Profiler response.")
        else:
            json_str = response_str
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        value_alignment_logger.error(f"Profiler agent failed to produce valid JSON. Raw output: {response_str}")
        agent_logger.error(f"[ERROR] Profiler agent failed to produce valid JSON. Raw output: {response_str}")
        return None  # type: ignore[return-value]

async def _run_hypothesizer_agent(profiler_analysis: dict, our_value_components: dict) -> Optional[dict]:
    """Agent 2: Uses the profile to hypothesize which of our value components are most relevant."""
    prompt = f"""
    You are a Strategy Hypothesizer. A company has been profiled, and now you must select which of our value components are the most promising fit.
    
    **Company Profile:**
    {json.dumps(profiler_analysis, indent=2)}

    **Our Value Components (with Importance Score 0-3):**
    {json.dumps(our_value_components, indent=2)}

    **Your Task:**
    Produce a JSON object with the following fields:
    - `hypothesis_rationale`: A brief explanation of your reasoning. Why are you choosing these components? Refer to the company's sentiment and our components' importance scores.
    - `shortlist`: A list of the names of the top 3-10 most relevant value components to investigate further.

    **JSON Output:**
    """
    value_alignment_logger.info("Running Hypothesizer Agent...")
    response_str = await chatgpt_generate(prompt, temperature=0.2, max_tokens=16384)
    
    # Check if chatgpt_generate returned an error
    if isinstance(response_str, str) and response_str.startswith("ERROR:"):
        error_msg = response_str.replace("ERROR:", "").strip()
        value_alignment_logger.error(f"Hypothesizer agent: ChatGPT client error: {error_msg if error_msg else 'Unknown error (empty message)'}")
        value_alignment_logger.error(f"Hypothesizer agent: Full error response: {repr(response_str)}")
        agent_logger.error(f"[ERROR] Hypothesizer agent: ChatGPT client error: {error_msg if error_msg else 'Unknown error (empty message)'}")
        agent_logger.error(f"[ERROR] Hypothesizer agent: Full error response: {repr(response_str)}")
        return {"error": f"ChatGPT client error: {error_msg if error_msg else 'Unknown error (empty message)'}"}
    
    try:
        # Try to extract JSON from ```json ... ``` code block
        match = re.search(r'```json\s*(\{.*?\})\s*```', response_str, re.DOTALL)
        if not match:
            # Fallback: Try to extract JSON from generic code block ``` ... ```
            match = re.search(r'```\s*(\{.*?\})\s*```', response_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            agent_logger.info("Extracted JSON from markdown block in Hypothesizer response.")
        else:
            json_str = response_str
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        value_alignment_logger.error(f"Hypothesizer agent failed to produce valid JSON. Raw output: {response_str}")
        return None  # type: ignore[return-value]

async def _run_final_aligner_agent(profiler_analysis: dict, hypothesis_analysis: dict, company_summary: str, our_value_components: dict, company_profile: Optional[dict] = None) -> dict:
    """Agent 3: Creates the final, detailed alignment matrix based on previous analysis."""
    summary_trunc = utils.safe_truncate_text(company_summary, 1500)

    # Prepare prospect data as a summary string
    prospect_data = json.dumps(profiler_analysis, indent=2)
    # Prepare value components as a summary string
    value_components_str = json.dumps(our_value_components, indent=2)

    # Get industry context from prospect data
    from app.ai.enhanced_prompts import enhanced_prompt_builder
    
    # Extract industry information from prospect data
    industry_name = "manufacturing"  # Default fallback
    try:
        # Try to extract industry from prospect data
        if "industry" in prospect_data.lower():
            # Simple extraction - in production, use more sophisticated parsing
            industry_name = "manufacturing"  # Placeholder for actual extraction
    except:
        pass
    
    # Ensure company_profile is available (load if missing)
    if company_profile is None:
        from app.core.company_context_manager import CompanyContextManager
        company_context = CompanyContextManager()
        company_profile = company_context.get_company_profile()
        if not isinstance(company_profile, dict):
            agent_logger.warning("Company profile not available or invalid, using empty dict")
            company_profile = {}
    
    # Build the enhanced industry-specific prompt with market intelligence
    prompt = await enhanced_prompt_builder.build_enhanced_value_alignment_prompt(
        prospect_data=prospect_data,
        company_profile=company_profile,
        value_components=value_components_str,
        industry_name=industry_name
    )
    agent_logger.info(f"Running Final Aligner Agent with enhanced industry-specific prompt (Industry: {industry_name})...")
    agent_logger.info(f"[DEBUG] Enhanced prompt includes market intelligence integration for {industry_name} industry")
    response_str = await chatgpt_generate(prompt, temperature=0.2, max_tokens=16384)

    # Check if chatgpt_generate returned an error
    if isinstance(response_str, str) and response_str.startswith("ERROR:"):
        error_msg = response_str.replace("ERROR:", "").strip()
        agent_logger.error(f"[ERROR] Final Aligner agent: ChatGPT client error: {error_msg}")
        agent_logger.error(f"[ERROR] Final Aligner agent: Full error response: {repr(response_str)}")
        value_alignment_logger.error(f"Final Aligner agent: ChatGPT client error: {error_msg}")
        value_alignment_logger.error(f"Final Aligner agent: Full error response: {repr(response_str)}")
        return {"error": f"ChatGPT client error: {error_msg if error_msg else 'Unknown error (empty message)'}", "alignment_matrix": []}

    if not response_str:
        agent_logger.error("Final Aligner agent returned an empty response.")
        return {"error": "The Final Aligner agent returned an empty response.", "alignment_matrix": []}

    # Enhanced parsing to find JSON within markdown code blocks
    # Log raw response for debugging (first and last 500 chars)
    response_preview = response_str[:500] + "..." if len(response_str) > 1000 else response_str
    agent_logger.info(f"[DEBUG] Final Aligner raw response (first 500 chars): {response_preview}")
    if len(response_str) > 1000:
        agent_logger.info(f"[DEBUG] Final Aligner raw response (last 500 chars): ...{response_str[-500:]}")
    
    try:
        match = re.search(r'```json\s*(\{.*?\})\s*```', response_str, re.DOTALL)
        if not match:
            match = re.search(r'```\s*(\{.*?\})\s*```', response_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            agent_logger.info("Extracted JSON from markdown block in Final Aligner response.")
            agent_logger.info(f"[DEBUG] Extracted JSON (first 500 chars): {json_str[:500]}")
        else:
            json_str = response_str
            agent_logger.info("No markdown code blocks found, using raw response as JSON")
        
        data = json.loads(json_str)
        agent_logger.info(f"[DEBUG] Parsed JSON type: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'N/A (not a dict)'}")
        
        if isinstance(data, dict) and 'alignment_matrix' in data:
            matrix = data.get('alignment_matrix', [])
            matrix_len = len(matrix) if isinstance(matrix, list) else 0
            agent_logger.info(f"[DEBUG] Final Aligner completed successfully with market intelligence integration for {industry_name} industry")
            agent_logger.info(f"[DEBUG] Alignment matrix contains {matrix_len} alignments")
            if matrix_len > 0:
                agent_logger.info(f"[DEBUG] First alignment sample: {json.dumps(matrix[0], indent=2)[:300] if isinstance(matrix, list) and len(matrix) > 0 else 'N/A'}")
            return data
        if isinstance(data, list):
            agent_logger.info(f"[DEBUG] Final Aligner returned a list with {len(data)} items - treating as alignment_matrix")
            agent_logger.info(f"[DEBUG] Final Aligner completed successfully with market intelligence integration for {industry_name} industry")
            agent_logger.info(f"[DEBUG] Alignment matrix contains {len(data)} alignments")
            return {"alignment_matrix": data}
        
        # Check if it's a dict without alignment_matrix - log what keys it has
        if isinstance(data, dict):
            agent_logger.warning(f"[DEBUG] Final Aligner produced dict without 'alignment_matrix' key. Available keys: {list(data.keys())}")
            agent_logger.warning(f"[DEBUG] Dict content preview: {json.dumps(data, indent=2)[:500]}")
        else:
            agent_logger.warning(f"[DEBUG] Final Aligner produced unexpected type: {type(data)}")
        
        agent_logger.warning(f"Final Aligner produced unexpected JSON structure")
        return {"error": "Final Aligner produced an unexpected JSON structure.", "alignment_matrix": []}
    except json.JSONDecodeError as e:
        agent_logger.error(f"[DEBUG] JSON decode error at position {e.pos}: {e.msg}")
        agent_logger.error(f"[DEBUG] Context around error: {response_str[max(0, e.pos-50):e.pos+50]}")
        agent_logger.error(f"Final Aligner failed to produce valid JSON. Raw output (first 1000 chars): {response_str[:1000]}")
        agent_logger.error(f"Final Aligner failed to produce valid JSON. Raw output length: {len(response_str)}")
        value_alignment_logger.error(f"Final Aligner failed to produce valid JSON. Error: {str(e)}, Response length: {len(response_str)}")
        return {
            "error": f"The Final Aligner agent failed to produce valid JSON: {str(e)}", 
            "alignment_matrix": []
        }
    except Exception as e:
        error_detail = str(e) if str(e) else f"{type(e).__name__} (no message)"
        agent_logger.error(f"[ERROR] Final Aligner agent: Unexpected exception: {type(e).__name__}: {error_detail}")
        agent_logger.error(f"[ERROR] Final Aligner agent: Exception details: {repr(e)}")
        agent_logger.error(f"[ERROR] Final Aligner agent: Response was: {repr(response_str[:500]) if response_str else 'None'}")
        value_alignment_logger.error(f"Final Aligner agent: Unexpected exception: {type(e).__name__}: {error_detail}")
        return {
            "error": f"Final Aligner agent raised an unexpected exception: {error_detail}",
            "alignment_matrix": []
        }

def build_eurostat_filter_prompt(company_summary, dataset_code, structure):
    prompt_context = f"You are an economic analyst selecting filters for a Eurostat query.\n"
    prompt_context += f"The query is for a company with the following profile:\n---\n{company_summary}\n---\n"
    prompt_context += f"You must select the best filter value for each dimension of the dataset '{dataset_code}'.\n"
    prompt_context += "Here are the available dimensions and their options (code: label):\n"
    for dim_code, dim_data in structure.items():
        if dim_code.lower() in ['geo', 'time', 'freq']:
            continue
        options_str = ", ".join([f"'{code}': '{label}'" for code, label in dim_data['values'].items()])
        prompt_context += f"- Dimension '{dim_code}' ({dim_data['label']}):\n  Options: {{{options_str}}}\n"
    prompt_context += "\nBased on the company profile, what is the single most relevant filter value for each dimension?"
    prompt_context += "\nOutput ONLY a JSON object where keys are the dimension codes and values are the chosen value codes."
    prompt_context += " Do not include geo, time, or freq dimensions in your output."
    prompt_context += "\nIMPORTANT: Only select from the allowed values listed above. Do NOT invent or guess codes."
    return prompt_context 