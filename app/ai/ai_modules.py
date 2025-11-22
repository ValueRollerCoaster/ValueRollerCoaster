import ollama
import logging
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv
import httpx
import json
from app.config import (
    OLLAMA_BASE_URL,
    MODEL,
    LOG_LEVEL,
    LOG_FORMAT,
    MAX_RETRIES,
    RETRY_DELAY,
    AI_TIMEOUT
)
import app.utils as utils
import re
from app.ai.prompts import PROMPT_TEMPLATES
from app.ai.gemini_client import gemini_client

# Load environment variables
load_dotenv()

# Configuration
MODEL = os.getenv('OLLAMA_MODEL', 'mistral')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
if not OLLAMA_BASE_URL:
    raise RuntimeError("OLLAMA_BASE_URL environment variable is not set. Please set it to the correct Ollama address.")

# Configure Ollama client
ollama.Client(host=OLLAMA_BASE_URL)

# Configure logging
# logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Main AI log file (renamed to log.log)
ai_logger = logging.getLogger("ai")
ai_handler = logging.FileHandler('logs/log.log', mode='a', encoding='utf-8')
ai_handler.setLevel(logging.INFO)
ai_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
ai_logger.addHandler(ai_handler)
ai_logger.propagate = False

# Separate API call log file
apicall_logger = logging.getLogger("apicall_log")
apicall_handler = logging.FileHandler('logs/apicall_log.log', mode='a', encoding='utf-8')
apicall_handler.setLevel(logging.INFO)
apicall_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
apicall_logger.addHandler(apicall_handler)
apicall_logger.propagate = False

class SafeDict(dict):
    def __missing__(self, key):
        logging.warning(f"[ai_generate] Missing key in prompt formatting: {key}")
        return ""

async def send_raw_ai_prompt(prompt: str, temperature: float = 0.7) -> str:
    """
    Generate a response from the AI model.
    Args:
        prompt: The prompt to send to the AI model
        temperature: Sampling temperature for the model (default 0.7)
    Returns:
        The AI model's response as a string
    """
    try:
        apicall_logger.info(f"Ollama API Request: {OLLAMA_BASE_URL}/api/generate, prompt: {prompt[:200]}, temperature: {temperature}")
        # Use HTTP request to Ollama API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=AI_TIMEOUT # Add a timeout to prevent hanging
            )
            response.raise_for_status() # Raise an exception for bad status codes
            apicall_logger.info(f"Ollama API Response: status={response.status_code}, body={response.text[:200]}")
            data = response.json()
            logger.info(f"Raw AI response data: {data}") # Log the raw data
            return data.get("response", "")
            
    except httpx.RequestError as e:
        apicall_logger.error(f"Ollama API Request Error: {str(e)}")
        logger.error(f"HTTPX Request Error during AI generation: {str(e)}")
        return ""
    except httpx.HTTPStatusError as e:
        apicall_logger.error(f"Ollama API HTTP Status Error: {e.response.status_code} - {e.response.text}")
        logger.error(f"HTTP Status Error from AI server: {e.response.status_code} - {e.response.text}")
        return ""
    except json.JSONDecodeError as e:
        apicall_logger.error(f"Ollama API JSON Decode Error: {str(e)}")
        logger.error(f"JSON Decode Error in AI response: {str(e)}\nRaw response text: {response.text}")
        return ""
    except Exception as e:
        apicall_logger.error(f"Ollama API Unexpected Error: {str(e)}")
        logger.error(f"Unexpected error generating AI response: {str(e)}")
        return ""

def get_prompt_template(task_type: str) -> Any:
    """Get the prompt template parts for the given task type."""
    template_info = PROMPT_TEMPLATES.get(task_type)
    if template_info is None:
        logger.error(f"No template found for task type: {task_type}")
        return None
    return template_info

def try_repair_json(bad_json: str) -> str:
    """Attempt to repair common JSON issues (missing commas, trailing commas, etc.)."""
    # Add a comma between closing brackets/quotes and opening quotes if missing
    repaired = re.sub(r'(\]|\")\s*(\")', r'\1, \2', bad_json)
    # Add a comma between closing brackets/quotes and opening curly braces if missing
    repaired = re.sub(r'(\]|\")\s*(\{)', r'\1, \2', repaired)
    # Add a comma between closing curly braces and opening quotes if missing
    repaired = re.sub(r'(\})\s*(\")', r'\1, \2', repaired)
    # Remove trailing commas before closing braces/brackets
    repaired = re.sub(r',\s*([}\]])', r'\1', repaired)
    return repaired

async def ai_generate(prompt: Optional[str] = None, prompt_template: Optional[str] = None, json_output: bool = True, retry_on_fail: bool = True, **params) -> Optional[str]:
    """Generate text using Gemini. Ollama/Mistral is no longer used."""
    if prompt_template:
        template = get_prompt_template(prompt_template)
        if not template:
            ai_logger.error(f"No template found for: {prompt_template}")
            return None
        try:
            prompt = "".join(template).format_map(SafeDict(params))
        except ValueError as ve:
            ai_logger.error(f"ValueError during prompt formatting: {ve}")
            ai_logger.error(f"Prompt template: {template}")
            ai_logger.error(f"Params: {params}")
            ai_logger.error(f"Param types: {{k: type(v) for k, v in params.items()}}")
            return None
    if not prompt:
        ai_logger.error("No prompt provided")
        return None
    ai_logger.info(f"AI PROMPT: {prompt}")
    try:
        response_text = await gemini_client(prompt, temperature=0.2, max_tokens=16000)
        ai_logger.info(f"Gemini AI response: {response_text}")
        return response_text
    except Exception as e:
        ai_logger.error(f"Gemini AI generation error: {e}")
        return None

def clean_ai_response_text(response_text: str) -> Optional[str]:
    """
    Extracts a JSON object from a string that might contain other text.
    Handles markdown code blocks and general text.
    """
    if not response_text or not isinstance(response_text, str):
        return None

    # First, remove any single-line comments //...
    response_text = re.sub(r"//.*", "", response_text)
    
    # Try to find JSON within markdown-style triple backticks
    match = re.search(r"```(json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if match:
        # If found in markdown, this is our JSON
        json_text = match.group(2)
    else:
        # If not in markdown, find the first and last curly brace
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_text = response_text[start_idx:end_idx + 1]
        else:
            # If no JSON object found at all
            logger.error("No valid JSON object found in response text.")
            logger.error(f"Response text: {response_text}")
            return None

    # Final check for and removal of instruction phrases that might be inside the JSON
    instruction_phrases_in_json = [
        'Output ONLY the JSON object',
        'Do not include any other text',
        'CRITICAL:',
        'IMPORTANT:',
        'JSON RULES:',
        'Example of valid JSON:',
        'Required JSON structure:',
        'Input:',
        'Now, analyze',
        'generate a valid JSON response',
        'Example response:',
        'Required JSON format:',
        '```json',
        '```'
    ]
    for phrase in instruction_phrases_in_json:
        json_text = json_text.replace(phrase, '')
    json_text = re.sub(r'```json\s*', '', json_text, flags=re.IGNORECASE)
    json_text = re.sub(r'```\s*$', '', json_text)
    # Remove newlines inside string values (replace newline followed by spaces with a space, only inside quotes)
    def fix_newlines_in_strings(match):
        return match.group(0).replace('\n', ' ').replace('\r', ' ')
    json_text = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', fix_newlines_in_strings, json_text)
    # Remove trailing commas before closing brackets/braces
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
    json_text = json_text.strip()
    return json_text

def validate_ai_response(response: Dict[str, Any], task_type: str) -> bool:
    """Validate the structure and content of the AI response based on task type."""
    if task_type == "value_waterfall":
        required_fields = ["company_info", "bom_cost", "manufacturing_cost", "value_add", "final_price", "value_bricks"]
        # Check for required top-level fields
        if not all(field in response for field in required_fields):
            logger.error(f"Value waterfall validation failed: Missing required top-level fields: {[field for field in required_fields if field not in response]}")
            return False

        # Validate company_info structure
        if not isinstance(response["company_info"], dict):
             logger.error("Value waterfall validation failed: company_info is not a dictionary.")
             return False
        required_company_fields = ["name", "industry", "size", "location"]
        if not all(field in response["company_info"] for field in required_company_fields):
             # Calculate missing fields
             missing_fields = [field for field in required_company_fields if field not in response["company_info"]]
             # Log the missing fields using the variable
             logger.error(f"Value waterfall validation failed: Missing required company_info fields: {missing_fields}")
             return False

        # Validate numerical fields are floats
        try:
            float(response["bom_cost"])
            float(response["manufacturing_cost"])
            float(response["value_add"])
            float(response["final_price"])
        except (ValueError, TypeError):
             logger.error("Value waterfall validation failed: Non-float value for bom_cost, manufacturing_cost, value_add, or final_price.")
             return False

        # Validate value_bricks structure
        if not isinstance(response["value_bricks"], list):
            logger.error("Value waterfall validation failed: value_bricks is not a list.")
            return False

        for i, brick in enumerate(response["value_bricks"]):
            if not isinstance(brick, dict):
                logger.error(f"Value waterfall validation failed: value_bricks item {i} is not a dictionary.")
                return False
            required_brick_fields = ["name", "description", "value"]
            if not all(field in brick for field in required_brick_fields):
                logger.error(f"Value waterfall validation failed: Missing required value_bricks fields in item {i}: {[field for field in required_brick_fields if field not in brick]}")
                return False
            try:
                # Attempt to convert to float, handling cases where it might be a string representation of a number
                brick_value = brick["value"]
                if isinstance(brick_value, str):
                    brick_value = float(brick_value.strip())
                else:
                    brick_value = float(brick_value)
                brick["value"] = brick_value # Update the value to ensure it's a float
            except (ValueError, TypeError):
                 logger.error(f"Value waterfall validation failed: Non-float value in value_bricks item {i}.")
                 return False

        return True # All value_waterfall checks passed

    elif task_type == "website_scanner":
        return validate_website_structure(response)
    elif task_type == "value_component":
        return validate_value_component(response)

    logger.warning(f"No validation implemented for task type: {task_type}")
    return True # Return True by default for unimplemented validation

def validate_website_structure(response: Dict[str, Any]) -> bool:
    """Validate the structure and content of the website scanner response."""
    try:
        if "structure" not in response:
            logger.error("Website structure validation failed: Missing 'structure' field")
            return False
            
        structure = response["structure"]
        required_fields = ["pages", "navigation", "contact_info"]
        if not all(field in structure for field in required_fields):
            logger.error(f"Website structure validation failed: Missing required fields: {[field for field in required_fields if field not in structure]}")
            return False
            
        # Validate pages
        if not isinstance(structure["pages"], list):
            logger.error("Website structure validation failed: 'pages' is not a list")
            return False
            
        for page in structure["pages"]:
            if not all(field in page for field in ["url", "title", "content"]):
                logger.error(f"Website structure validation failed: Missing required page fields: {[field for field in ['url', 'title', 'content'] if field not in page]}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error validating website structure: {str(e)}")
        return False

def validate_value_component(response: Dict[str, Any]) -> bool:
    """Validate the structure and content of the value component response."""
    try:
        if "component" not in response:
            logger.error("Value component validation failed: Missing 'component' field")
            return False
            
        component = response["component"]
        required_fields = ["category", "name", "value", "benefits", "examples", "metrics"]
        if not all(field in component for field in required_fields):
            logger.error(f"Value component validation failed: Missing required fields: {[field for field in required_fields if field not in component]}")
            return False
            
        # Validate lists
        for field in ["benefits", "examples", "metrics"]:
            if not isinstance(component[field], list):
                logger.error(f"Value component validation failed: '{field}' is not a list")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error validating value component: {str(e)}")
        return False

async def create_embedding(text: str) -> List[float]:
    """Create an embedding for the given text using Ollama."""
    try:
        logger.info(f"Creating embedding for text (first 50 chars): {text[:50]}...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": MODEL,
                    "prompt": text
                },
                timeout=AI_TIMEOUT # Use configurable timeout
            )
        response.raise_for_status() # Raise an HTTPStatusError for bad responses (4xx or 5xx)
        data = response.json()
        
        # Ensure we get a vector of the correct dimension (1536)
        vector = data.get("embedding", [])
        if len(vector) != 1536:
            logger.warning(f"Unexpected embedding dimension: {len(vector)}. Expected 1536.")
            # Attempt to pad or truncate if dimension is unexpected but close, or return zero vector
            if 1000 < len(vector) < 2000:
                 logger.warning("Attempting to adjust embedding dimension.")
                 if len(vector) > 1536:
                     vector = vector[:1536]
                 else:
                     vector.extend([0.0] * (1536 - len(vector)))
                 logger.warning(f"Adjusted vector dimension to {len(vector)}.")
            else:
                 logger.error("Embedding dimension significantly different from 1536. Returning zero vector.")
                 vector = [0.0] * 1536
        
        logger.info(f"Successfully created embedding with dimension: {len(vector)}")
        return vector
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error during embedding creation: {e.response.status_code} - {e.response.text}")
        return [0.0] * 1536
    except httpx.RequestError as e:
        logger.error(f"Request error during embedding creation: {str(e)}")
        return [0.0] * 1536
    except Exception as e:
        logger.error(f"Error creating embedding: {type(e).__name__} - {str(e)}")
        return [0.0] * 1536 

async def generate_ai_response(task_type: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate AI response for the given task type and parameters."""
    try:
        # Get prompt template
        template = get_prompt_template(task_type)
        if not template:
            logger.error(f"No template found for task type: {task_type}")
            return None
            
        # Format prompt
        prompt = "".join(template["parts"]).format(**params)
        
        # Generate response
        response_text = await ai_generate(prompt)
        if not response_text:
            logger.error("Failed to generate AI response")
            return None
            
        # Clean and parse response
        cleaned_text = clean_ai_response_text(response_text)
        if not cleaned_text:
            logger.error("Failed to clean AI response")
            return None
            
        try:
            response = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return None
            
        # Validate response
        if not validate_ai_response(response, task_type):
            logger.error("AI response validation failed")
            return None
            
        return response
        
    except Exception as e:
        logger.error(f"Error generating AI response: {str(e)}")
        return None 

# --- Eurostat persona async AI function (Ollama/local model) ---
from app.ai.prompts import EUROSTAT_PERSONA_PROMPT

async def ai_generate_eurostat_persona(industry, eurostat_context):
    """
    Calls the local AI model to generate a buyer persona using a robust, context-rich prompt.
    Assumptions:
      - industry: string, e.g. "Pharmaceuticals"
      - eurostat_context: string, generated by eurostat_prompt_context(), listing valid datasets/dimensions/values
    Returns:
      - String: AI output as a JSON string
    """
    prompt = EUROSTAT_PERSONA_PROMPT.format(
        industry=industry,
        eurostat_context=eurostat_context
    )
    return await ai_generate(prompt=prompt, json_output=True)
# --- End Eurostat persona async AI function --- 