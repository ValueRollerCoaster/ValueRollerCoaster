import os
import httpx
import asyncio
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import deterministic configuration
try:
    from app.config import (
        GEMINI_TEMPERATURE, GEMINI_SEED, GEMINI_TOP_P, 
        GEMINI_TOP_K, GEMINI_MAX_TOKENS
    )
except ImportError:
    # Fallback values if config import fails
    GEMINI_TEMPERATURE = 0.0
    GEMINI_SEED = 42
    GEMINI_TOP_P = 1.0
    GEMINI_TOP_K = 1
    GEMINI_MAX_TOKENS = 4000

GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

# Create dedicated Gemini logger
def setup_gemini_logger():
    """Setup dedicated logger for Gemini API calls"""
    gemini_logger = logging.getLogger('gemini_model')
    gemini_logger.setLevel(logging.INFO)
    
    # Create file handler for Gemini-specific log file
    log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'gemini_model.log')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter matching ChatGPT style
    formatter = logging.Formatter(
        '[%(asctime)s] [PID %(process)d] [%(levelname)s] [%(funcName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Prevent propagation to root logger
    gemini_logger.propagate = False
    
    # Add handler only if not already added
    if not gemini_logger.handlers:
        gemini_logger.addHandler(file_handler)
    
    return gemini_logger

# Initialize Gemini logger
gemini_logger = setup_gemini_logger()

# --- Google Generative AI SDK with Google Search Grounding ---
# Note: Google Search grounding requires the newer 'google-genai' package.
# The older 'google-generativeai' package may not support GoogleSearch().
# If you need Google Search grounding, install: pip install google-genai
try:
    # Try newer google-genai package first (for Google Search grounding)
    # type: ignore - Package may not be installed, handled by ImportError below
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
    _GENAI_AVAILABLE = True
    _GENAI_SDK_TYPE = "new"
except ImportError:
    # If google-genai is not available, Google Search grounding features won't work
    # The functions using types.Tool(google_search=...) will return errors
    _GENAI_AVAILABLE = False
    _GENAI_SDK_TYPE = None
    genai = None
    types = None
    # Use root logger for this warning since gemini_logger may not be initialized yet
    logging.warning(
        "[gemini_client] 'google-genai' package not found. "
        "Google Search grounding features require: pip install google-genai"
    )

async def gemini_client(prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None, model: Optional[str] = None, pid: int = 0) -> str:
    """
    Gemini client with deterministic configuration for consistent results.
    Includes retry logic for 503 (overloaded) errors with exponential backoff.
    
    Args:
        prompt: The input prompt
        temperature: Override temperature (uses config default if None)
        max_tokens: Override max tokens (uses config default if None)
        model: Override model (uses config default if None)
        pid: Process ID for logging (optional)
    """
    if not GEMINI_API_KEY:
        gemini_logger.error(f"[PID {pid}] [gemini_client] GEMINI_API_KEY environment variable not set.")
        return "ERROR: GEMINI_API_KEY environment variable not set."
    
    import asyncio
    
    # Use deterministic defaults from config
    temperature = temperature if temperature is not None else GEMINI_TEMPERATURE
    max_tokens = max_tokens if max_tokens is not None else GEMINI_MAX_TOKENS
    model_to_use = model or GEMINI_MODEL
    
    gemini_logger.info(f"[PID {pid}] [gemini_client] Using deterministic config - Temp: {temperature}, MaxTokens: {max_tokens}, Seed: {GEMINI_SEED}, Model: {model_to_use}")
    
    api_url = GEMINI_API_URL_TEMPLATE.format(model_to_use)
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    
    # Build generation config with deterministic parameters
    generation_config = {
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
        "topP": GEMINI_TOP_P,
        "topK": GEMINI_TOP_K
    }
    
    # Add seed if supported by the model
    if GEMINI_SEED is not None:
        generation_config["seed"] = GEMINI_SEED
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation_config
    }
    
    max_retries = 3
    base_delay = 2  # Start with 2 seconds
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(api_url, headers=headers, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
                # Defensive: check for expected structure
                if (
                    "candidates" in data and
                    data["candidates"] and
                    "content" in data["candidates"][0] and
                    "parts" in data["candidates"][0]["content"] and
                    data["candidates"][0]["content"]["parts"] and
                    "text" in data["candidates"][0]["content"]["parts"][0]
                ):
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    finish_reason = data["candidates"][0].get("finishReason", "UNKNOWN")
                    if finish_reason == "MAX_TOKENS":
                        gemini_logger.warning(f"[PID {pid}] [gemini_client] Gemini response truncated (MAX_TOKENS). Returning partial content.")
                    
                    # Extract token usage if available
                    token_usage = {}
                    if "usageMetadata" in data:
                        usage = data["usageMetadata"]
                        token_usage = {
                            "prompt_tokens": usage.get("promptTokenCount", 0),
                            "completion_tokens": usage.get("candidatesTokenCount", 0),
                            "total_tokens": usage.get("totalTokenCount", 0)
                        }
                        gemini_logger.info(f"[PID {pid}] [gemini_client] SUCCESS - ResponseLength: {len(text)} chars, FinishReason: {finish_reason}, Tokens: {token_usage.get('total_tokens', 0)} (Prompt: {token_usage.get('prompt_tokens', 0)}, Completion: {token_usage.get('completion_tokens', 0)})")
                    else:
                        gemini_logger.info(f"[PID {pid}] [gemini_client] SUCCESS - ResponseLength: {len(text)} chars, FinishReason: {finish_reason}")
                    return text
                else:
                    finish_reason = (
                        data["candidates"][0].get("finishReason", "UNKNOWN")
                        if "candidates" in data and data["candidates"] else "NO_CANDIDATES"
                    )
                    gemini_logger.error(f"[PID {pid}] [gemini_client] Unexpected API response (finishReason={finish_reason}): {data}")
                    # Try to return any partial text if available
                    try:
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        gemini_logger.warning(f"[PID {pid}] [gemini_client] Returning partial text from unexpected response structure.")
                        return text
                    except Exception:
                        return f"ERROR: Unexpected API response (finishReason={finish_reason}): {data}"
        except httpx.HTTPStatusError as e:
            error_str = str(e)
            # Check if it's a 503 overloaded error
            is_overloaded = e.response.status_code == 503 or "503" in error_str or "overloaded" in error_str.lower() or "UNAVAILABLE" in error_str or "Service Unavailable" in error_str
            
            if is_overloaded and attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s
                delay = base_delay * (2 ** attempt)
                gemini_logger.warning(f"[PID {pid}] [gemini_client] Model overloaded (503), retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {error_str[:100]}")
                await asyncio.sleep(delay)
                continue
            else:
                # Final attempt failed or non-retryable error
                gemini_logger.error(f"[PID {pid}] [gemini_client] HTTP_ERROR - Status: {e.response.status_code}, Error: {e}")
                return f"ERROR: {e}"
        except Exception as e:
            error_str = str(e)
            # Check if it's a 503 overloaded error (in case it's wrapped differently)
            is_overloaded = "503" in error_str or "overloaded" in error_str.lower() or "UNAVAILABLE" in error_str or "Service Unavailable" in error_str
            
            if is_overloaded and attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s
                delay = base_delay * (2 ** attempt)
                gemini_logger.warning(f"[PID {pid}] [gemini_client] Model overloaded (503), retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {error_str[:100]}")
                await asyncio.sleep(delay)
                continue
            else:
                # Final attempt failed or non-retryable error
                gemini_logger.error(f"[PID {pid}] [gemini_client] UNEXPECTED_ERROR - {e}")
                return f"ERROR: {e}"
    
    # Should not reach here, but just in case
    return "ERROR: Max retries exceeded"

def get_grounded_company_summary(website_url: str, model: str = "gemini-2.5-flash", pid: int = 0) -> str:
    """
    Uses Gemini with Google Search grounding to fetch and summarize up-to-date company information from the web.
    Returns a concise, factual summary for the given website URL.
    Includes retry logic for 503 (overloaded) errors with exponential backoff.
    
    Args:
        website_url: The website URL to analyze
        model: Gemini model to use
        pid: Process ID for logging (optional)
    """
    if not _GENAI_AVAILABLE:
        gemini_logger.error(f"[PID {pid}] [get_grounded_company_summary] google-generativeai SDK is not installed.")
        return "ERROR: google-generativeai SDK is not installed."
    
    # Type guard: ensure genai and types are not None
    if genai is None or types is None:
        gemini_logger.error(f"[PID {pid}] [get_grounded_company_summary] google-generativeai SDK is not installed.")
        return "ERROR: google-generativeai SDK is not installed."
    
    import time
    
    max_retries = 3
    base_delay = 2  # Start with 2 seconds
    
    for attempt in range(max_retries):
        try:
            client = genai.Client()
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            
            # Use deterministic configuration
            config = types.GenerateContentConfig(
                tools=[grounding_tool],
                temperature=GEMINI_TEMPERATURE,
                top_p=GEMINI_TOP_P,
                top_k=GEMINI_TOP_K,
                max_output_tokens=GEMINI_MAX_TOKENS
            )
            
            # Add seed if supported
            if GEMINI_SEED is not None:
                config.seed = GEMINI_SEED
            
            prompt = (
                f"Summarize the business, products, and value proposition of the company that owns and operates the website at {website_url}. "
                "Focus ONLY on the company that controls this specific domain. "
                "Do not analyze any other companies mentioned in search results. "
                "Use up-to-date information from the web. Be concise and factual. "
                "Start by clearly identifying the company name and confirming it owns this website."
            )
            gemini_logger.info(f"[PID {pid}] [get_grounded_company_summary] START - Website: {website_url}, Model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            gemini_logger.info(f"[PID {pid}] [get_grounded_company_summary] SUCCESS - ResponseLength: {len(response.text) if response.text else 0} chars")
            return response.text
            
        except Exception as e:
            error_str = str(e)
            # Check if it's a 503 overloaded error
            is_overloaded = "503" in error_str or "overloaded" in error_str.lower() or "UNAVAILABLE" in error_str
            
            if is_overloaded and attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s
                delay = base_delay * (2 ** attempt)
                gemini_logger.warning(f"[PID {pid}] [get_grounded_company_summary] Model overloaded (503), retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {error_str[:100]}")
                time.sleep(delay)
                continue
            else:
                # Final attempt failed or non-retryable error
                gemini_logger.error(f"[PID {pid}] [get_grounded_company_summary] ERROR - {e}")
                return f"ERROR: {e}"
    
    # Should not reach here, but just in case
    return "ERROR: Max retries exceeded"


def get_grounded_company_summary_with_explicit_search(website_url: str, model: str = "gemini-2.5-flash", pid: int = 0) -> str:
    """
    Uses Gemini with Google Search grounding and explicit search instructions.
    This version explicitly instructs Gemini to use web search instead of direct website access.
    Returns a comprehensive company analysis for the given website URL.
    Includes retry logic for 503 (overloaded) errors with exponential backoff.
    
    Args:
        website_url: The website URL to analyze
        model: Gemini model to use
        pid: Process ID for logging (optional)
    """
    if not _GENAI_AVAILABLE:
        gemini_logger.error(f"[PID {pid}] [get_grounded_company_summary_with_explicit_search] google-generativeai SDK is not installed.")
        return "ERROR: google-generativeai SDK is not installed."
    
    # Type guard: ensure genai and types are not None
    if genai is None or types is None:
        gemini_logger.error(f"[PID {pid}] [get_grounded_company_summary_with_explicit_search] google-generativeai SDK is not installed.")
        return "ERROR: google-generativeai SDK is not installed."
    
    import time
    
    max_retries = 3
    base_delay = 2  # Start with 2 seconds
    
    for attempt in range(max_retries):
        try:
            client = genai.Client()
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            
            # Use deterministic configuration
            config = types.GenerateContentConfig(
                tools=[grounding_tool],
                temperature=GEMINI_TEMPERATURE,
                top_p=GEMINI_TOP_P,
                top_k=GEMINI_TOP_K,
                max_output_tokens=GEMINI_MAX_TOKENS
            )
            
            # Add seed if supported
            if GEMINI_SEED is not None:
                config.seed = GEMINI_SEED
            
            prompt = (
                f"Use Google Search to find comprehensive information about the company at {website_url}. "
                "Search for:\n"
                "- Company name and business information\n"
                "- Products and services\n"
                "- Recent news and announcements\n"
                "- Industry information\n"
                "- Company profiles on business directories\n"
                "- Press releases and official communications\n"
                "\n"
                "**CRITICAL INSTRUCTIONS:**\n"
                "- Do NOT attempt to access the website directly\n"
            "- Use ONLY Google Search results from multiple sources\n"
            "- Search for information even if the website might be temporarily unavailable\n"
            "- Find information from news articles, Wikipedia, company profiles, and other indexed sources\n"
            f"- Focus ONLY on the company that owns and operates this specific domain: {website_url}\n"
            "- Do not analyze any other companies mentioned in search results\n"
            "\n"
            "Provide a comprehensive, structured analysis covering:\n"
            "1. Company overview (name, history, size, location)\n"
            "2. Products and services portfolio\n"
            "3. Target customers and industries served\n"
            "4. Value propositions and competitive advantages\n"
            "5. Market positioning and brand messaging\n"
            "6. Business model and revenue streams\n"
            "7. Recent developments and news\n"
            "\n"
            "Be specific and detailed. Include direct quotes and citations from search results where possible. "
            "Start by clearly identifying the company name and confirming it owns this website."
        )
        
            gemini_logger.info(f"[PID {pid}] [get_grounded_company_summary_with_explicit_search] START - Website: {website_url}, Model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            )
            gemini_logger.info(f"[PID {pid}] [get_grounded_company_summary_with_explicit_search] SUCCESS - ResponseLength: {len(response.text) if response.text else 0} chars")
            return response.text
            
        except Exception as e:
            error_str = str(e)
            # Check if it's a 503 overloaded error
            is_overloaded = "503" in error_str or "overloaded" in error_str.lower() or "UNAVAILABLE" in error_str
            
            if is_overloaded and attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 8s
                delay = base_delay * (2 ** attempt)
                gemini_logger.warning(f"[PID {pid}] [get_grounded_company_summary_with_explicit_search] Model overloaded (503), retrying in {delay}s (attempt {attempt + 1}/{max_retries}): {error_str[:100]}")
                time.sleep(delay)
                continue
            else:
                # Final attempt failed or non-retryable error
                gemini_logger.error(f"[PID {pid}] [get_grounded_company_summary_with_explicit_search] ERROR - {e}")
                return f"ERROR: {e}"
    
    # Should not reach here, but just in case
    return "ERROR: Max retries exceeded"


async def gemini_client_with_grounding(prompt: str, temperature: Optional[float] = None, 
                                      max_tokens: Optional[int] = None, model: Optional[str] = None, pid: int = 0) -> str:
    """
    Gemini client with Google Search grounding explicitly enabled.
    Use this for prompts that should leverage Google Search instead of direct website access.
    
    Args:
        prompt: The input prompt (should include instructions to use web search)
        temperature: Override temperature (uses config default if None)
        max_tokens: Override max tokens (uses config default if None)
        model: Override model (uses config default if None)
        pid: Process ID for logging (optional)
    """
    if not _GENAI_AVAILABLE:
        gemini_logger.error(f"[PID {pid}] [gemini_client_with_grounding] google-generativeai SDK is not installed.")
        return "ERROR: google-generativeai SDK is not installed."
    
    # Type guard: ensure genai and types are not None
    if genai is None or types is None:
        gemini_logger.error(f"[PID {pid}] [gemini_client_with_grounding] google-generativeai SDK is not installed.")
        return "ERROR: google-generativeai SDK is not installed."
    
    if not GEMINI_API_KEY:
        gemini_logger.error(f"[PID {pid}] [gemini_client_with_grounding] GEMINI_API_KEY environment variable not set.")
        return "ERROR: GEMINI_API_KEY environment variable not set."
    
    try:
        client = genai.Client()
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        
        # Use deterministic configuration
        temperature = temperature if temperature is not None else GEMINI_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else GEMINI_MAX_TOKENS
        model_to_use = model or GEMINI_MODEL
        
        gemini_logger.info(f"[PID {pid}] [gemini_client_with_grounding] START - Model: {model_to_use}, Temp: {temperature}, MaxTokens: {max_tokens}, Grounding: Enabled")
        
        config = types.GenerateContentConfig(
            tools=[grounding_tool],  # Explicitly enable Google Search
            temperature=temperature,
            top_p=GEMINI_TOP_P,
            top_k=GEMINI_TOP_K,
            max_output_tokens=max_tokens
        )
        
        # Add seed if supported
        if GEMINI_SEED is not None:
            config.seed = GEMINI_SEED
        
        response = client.models.generate_content(
            model=model_to_use,
            contents=prompt,
            config=config,
        )
        gemini_logger.info(f"[PID {pid}] [gemini_client_with_grounding] SUCCESS - ResponseLength: {len(response.text) if response.text else 0} chars")
        return response.text
    except Exception as e:
        gemini_logger.error(f"[PID {pid}] [gemini_client_with_grounding] ERROR - {e}")
        return f"ERROR: {e}" 