import httpx
import logging
import os
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv
from app.config import DEBUG_MODE, DEBUG_AI_PROCESSING

load_dotenv()

async def mistral_client(prompt: str, model: Optional[str] = None, json_output: bool = False, temperature: Optional[float] = None, seed: Optional[int] = None, base_url: Optional[str] = None) -> str:
    """
    Sends a prompt to the local Mistral model (Ollama or similar) and returns the response as a string.
    Uses the OLLAMA_BASE_URL environment variable. If not set, raises an error.
    """
    # Ensure model is always a string (never None)
    model = model or os.environ.get("OLLAMA_MODEL", "mistral:latest")
    if not model:
        error_msg = "[mistral_client] Model configuration is invalid."
        logging.error(error_msg)
        return error_msg
    if not base_url:
        base_url = os.environ.get("OLLAMA_BASE_URL")
    if not base_url:
        error_msg = "[mistral_client] OLLAMA_BASE_URL environment variable is not set. Please set it to the correct Ollama address."
        logging.error(error_msg)
        return error_msg
    
    # Type narrowing: base_url is guaranteed to be str here
    if not isinstance(base_url, str):
        error_msg = "[mistral_client] Invalid base_url configuration."
        logging.error(error_msg)
        return error_msg
    url = f"{base_url}/api/generate"
    # Cap prompt/context size to 3000 characters
    if len(prompt) > 3000:
        logging.warning(f"[mistral_client] Prompt too long ({len(prompt)} chars), truncating to 3000.")
        prompt = prompt[:3000]
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    if json_output:
        payload['format'] = 'json'
    if temperature is not None:
        payload['temperature'] = temperature
    if seed is not None:
        payload['seed'] = seed
    
    retries = 2
    backoff = [0.5, 1.0]
    for attempt in range(retries + 1):
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # First check if Ollama is running and get available models
                try:
                    tags_response = await client.get(f"{base_url}/api/tags", timeout=5.0)
                    tags_response.raise_for_status()
                    available_models = [m.get('name') for m in tags_response.json().get('models', [])]
                    logging.info(f"[mistral_client] Ollama service is running. Available models: {available_models}")

                    model_names = set(available_models)
                    # Type narrowing: model is guaranteed to be str at this point
                    if not isinstance(model, str):
                        error_msg = "[mistral_client] Model name is invalid."
                        logging.error(error_msg)
                        return error_msg
                    requested_base = model.split(':')[0]
                    if model not in model_names and requested_base not in [m.split(':')[0] for m in available_models]:
                        mistral_models = [m for m in available_models if 'mistral' in m.lower()]
                        if mistral_models:
                            selected_model = mistral_models[0]
                            logging.warning(f"[mistral_client] Requested model '{model}' not found. Using available Mistral model: '{selected_model}' instead.")
                            model = selected_model
                            payload["model"] = model
                        else:
                            error_msg = f"[ERROR] No Mistral model is available in Ollama. Please run `ollama pull mistral` or `ollama pull mistral:latest`."
                            logging.error(f"[mistral_client] {error_msg}")
                            return error_msg
                    else:
                        logging.info(f"[mistral_client] Using model: {model}")

                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logging.error(f"[mistral_client] Ollama service is not running or not accessible at {base_url}. Full error: {e}")
                    if attempt < retries:
                        await asyncio.sleep(backoff[attempt])
                        continue
                    return f"[ERROR] Ollama service is not running or not accessible. Check the logs for details."

                response = await client.post(url, json=payload)
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as e:
                    logging.error(f"[mistral_client] HTTP error: {e.response.status_code} - {e.response.text}")
                    if attempt < retries:
                        await asyncio.sleep(backoff[attempt])
                        continue
                    return f"[ERROR] Ollama returned HTTP {e.response.status_code}: {e.response.text}"
                data = response.json()
                if DEBUG_MODE or DEBUG_AI_PROCESSING:
                    logging.debug(f"[mistral_client] Raw response: {json.dumps(data)[:200]}...")
                if "response" in data:
                    return data["response"]
                logging.warning(f"[mistral_client] Unexpected response format: {json.dumps(data)[:200]}...")
                return str(data)
            except httpx.TimeoutException:
                error_msg = "[ERROR] Mistral API call timed out"
                logging.error(f"[mistral_client] {error_msg}")
                if attempt < retries:
                    await asyncio.sleep(backoff[attempt])
                    continue
                return error_msg
            except httpx.RequestError as e:
                error_msg = f"[ERROR] Mistral API request failed: {e}. Check if the Ollama server is running and accessible at {base_url}."
                logging.error(f"[mistral_client] {error_msg}", exc_info=True)
                if attempt < retries:
                    await asyncio.sleep(backoff[attempt])
                    continue
                return error_msg
            except json.JSONDecodeError as e:
                error_msg = f"[ERROR] Failed to parse Mistral API response: {e}"
                logging.error(f"[mistral_client] {error_msg}")
                if attempt < retries:
                    await asyncio.sleep(backoff[attempt])
                    continue
                return error_msg
            except Exception as e:
                logging.error(f"[mistral_client] Unexpected error in Mistral API call: {e}", exc_info=True)
                if attempt < retries:
                    await asyncio.sleep(backoff[attempt])
                    continue
                return f"[ERROR] Unexpected error in Mistral API call: {e}"
    
    # Fallback return if loop completes without returning (should never happen, but satisfies type checker)
    return "[ERROR] Mistral API call failed after all retries." 