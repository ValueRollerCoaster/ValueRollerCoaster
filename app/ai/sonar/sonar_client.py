"""
Sonar Client
Main API client for Sonar integration with clean error handling and fallbacks.
Uses Perplexity API with OpenAI client library.
"""

import os
import asyncio
import logging
import httpx
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import deterministic configuration
try:
    from app.config import (
        SONAR_API_KEY, SONAR_MODEL, SONAR_TEMPERATURE, 
        SONAR_MAX_TOKENS, SONAR_SEED
    )
except ImportError:
    # Fallback values if config import fails
    SONAR_API_KEY = os.environ.get("SONAR_API_KEY")
    SONAR_MODEL = "sonar-pro"  # Updated to correct model name
    SONAR_TEMPERATURE = 0.0
    SONAR_MAX_TOKENS = 4000
    SONAR_SEED = 42

# Create dedicated Sonar logger
def setup_sonar_logger():
    """Setup dedicated logger for Sonar API calls"""
    sonar_logger = logging.getLogger('sonar_model')
    sonar_logger.setLevel(logging.INFO)
    
    # Create file handler for Sonar-specific log file
    log_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs', 'sonar_model.log')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter matching ChatGPT style
    formatter = logging.Formatter(
        '[%(asctime)s] [PID %(process)d] [%(levelname)s] [%(funcName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Prevent propagation to root logger
    sonar_logger.propagate = False
    
    # Add handler only if not already added
    if not sonar_logger.handlers:
        sonar_logger.addHandler(file_handler)
    
    return sonar_logger

# Initialize Sonar logger
sonar_logger = setup_sonar_logger()

# Module logger for non-API-call logs (initialization, etc.)
logger = logging.getLogger(__name__)

class SonarClient:
    """Sonar API client using Perplexity API with deterministic configuration and error handling"""
    
    def __init__(self):
        self.api_key = SONAR_API_KEY
        self.model = SONAR_MODEL
        self.base_url = "https://api.perplexity.ai/chat/completions"
        
        if not self.api_key:
            logger.warning("[SonarClient] SONAR_API_KEY not configured. Sonar features will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            # Log API key info for debugging (without exposing full key)
            api_key_info = f"Length: {len(self.api_key)}, Prefix: {self.api_key[:10]}..." if self.api_key else "None"
            logger.info(f"[SonarClient] Initialized with model: {self.model}, API Key: {api_key_info}")
    
    async def generate_response(self, prompt: str, temperature: Optional[float] = None, 
                               max_tokens: Optional[int] = None, pid: int = 0,
                               search_domain_filter: Optional[List[str]] = None) -> str:
        """
        Generate response using Sonar with deterministic configuration.
        
        Args:
            prompt: The input prompt
            temperature: Override temperature (uses config default if None)
            max_tokens: Override max tokens (uses config default if None)
            pid: Process ID for logging
            search_domain_filter: List of domains to filter search results (Perplexity API)
            
        Returns:
            Sonar response text or error message
        """
        if not self.enabled:
            return "ERROR: Sonar is not configured"
        
        start_time = datetime.now()
        
        # Use deterministic defaults from config
        temperature = temperature if temperature is not None else SONAR_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else SONAR_MAX_TOKENS
        
        sonar_logger.info(f"[PID {pid}] [SonarClient] START - Model: {self.model}, Temp: {temperature}, MaxTokens: {max_tokens}")
        
        try:
            # Build messages with system prompt for deterministic behavior
            messages = [
                {"role": "system", "content": "Be precise and concise. Provide accurate, factual information."},
                {"role": "user", "content": prompt}
            ]
            
            # Build payload with correct Perplexity API structure
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add Perplexity-specific parameters based on documentation
            # Enable domain filtering to focus search results on specific domains
            if search_domain_filter:
                payload["search_domain_filter"] = search_domain_filter
                sonar_logger.info(f"[PID {pid}] [SonarClient] Domain filter enabled: {search_domain_filter}")
            
            sonar_logger.info(f"[PID {pid}] [SonarClient] Using Perplexity API" + (" (domain filtering enabled)" if search_domain_filter else ""))
            
            # Make direct HTTP call to Perplexity API
            # CRITICAL: Cloudflare is blocking requests - need proper headers
            # Perplexity API requires standard HTTP headers to pass Cloudflare protection
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "python-httpx/0.25.0",  # Use httpx user agent
                "Accept": "application/json"
            }
            
            # Log request details for debugging
            sonar_logger.debug(f"[PID {pid}] [SonarClient] Request URL: {self.base_url}")
            api_key_preview = self.api_key[:10] + "..." if self.api_key and len(self.api_key) >= 10 else "N/A"
            sonar_logger.debug(f"[PID {pid}] [SonarClient] Request headers: Authorization=Bearer {api_key_preview}, Content-Type=application/json")
            sonar_logger.debug(f"[PID {pid}] [SonarClient] Request payload keys: {list(payload.keys())}")
            
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(30.0, connect=10.0)
            ) as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=httpx.Timeout(30.0, connect=10.0)
                )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the JSON response
            response_data = response.json()
            
            # Extract the response text
            if response_data.get("choices") and response_data["choices"][0].get("message"):
                response_text = response_data["choices"][0]["message"]["content"]
                if response_text is None:
                    sonar_logger.error(f"[PID {pid}] [SonarClient] ERROR - Response content is None")
                    return "ERROR: Response content is None"
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Extract token usage if available
                token_usage = {}
                if "usage" in response_data:
                    usage = response_data["usage"]
                    token_usage = {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    }
                    sonar_logger.info(f"[PID {pid}] [SonarClient] SUCCESS - Duration: {duration:.2f}s, ResponseLength: {len(response_text)} chars, Tokens: {token_usage.get('total_tokens', 0)} (Prompt: {token_usage.get('prompt_tokens', 0)}, Completion: {token_usage.get('completion_tokens', 0)})")
                else:
                    sonar_logger.info(f"[PID {pid}] [SonarClient] SUCCESS - Duration: {duration:.2f}s, ResponseLength: {len(response_text)} chars")
                
                # Log citations if available
                if "citations" in response_data:
                    sonar_logger.info(f"[PID {pid}] [SonarClient] Citations found: {len(response_data['citations'])}")
                
                return response_text
            else:
                sonar_logger.error(f"[PID {pid}] [SonarClient] ERROR - No choices in response")
                return "ERROR: No choices in response"
                    
        except httpx.HTTPStatusError as e:
            # Enhanced error logging for 401 errors to help diagnose authentication issues
            if e.response.status_code == 401:
                sonar_logger.error(f"[PID {pid}] [SonarClient] AUTHENTICATION_ERROR - 401 Unauthorized")
                sonar_logger.error(f"[PID {pid}] [SonarClient] API Key present: {self.api_key is not None}")
                sonar_logger.error(f"[PID {pid}] [SonarClient] API Key length: {len(self.api_key) if self.api_key else 0}")
                sonar_logger.error(f"[PID {pid}] [SonarClient] API Key prefix: {self.api_key[:10] if self.api_key and len(self.api_key) >= 10 else 'N/A'}")
                sonar_logger.error(f"[PID {pid}] [SonarClient] Model: {self.model}")
                sonar_logger.error(f"[PID {pid}] [SonarClient] Base URL: {self.base_url}")
                sonar_logger.error(f"[PID {pid}] [SonarClient] Response: {e.response.text[:500] if e.response.text else 'No response body'}")
                sonar_logger.error(f"[PID {pid}] [SonarClient] Please verify SONAR_API_KEY is valid and not expired")
            else:
                sonar_logger.error(f"[PID {pid}] [SonarClient] HTTP_ERROR - Status: {e.response.status_code}, Response: {e.response.text[:500]}")
            return f"ERROR: HTTP {e.response.status_code} - {e.response.text[:500] if e.response.text else 'No response body'}"
        except httpx.RequestError as e:
            sonar_logger.error(f"[PID {pid}] [SonarClient] REQUEST_ERROR - {e}")
            return f"ERROR: Request failed - {e}"
        except Exception as e:
            sonar_logger.error(f"[PID {pid}] [SonarClient] UNEXPECTED_ERROR - {e}")
            return f"ERROR: {e}"
    
    async def is_available(self) -> bool:
        """Check if Sonar is available and configured"""
        return self.enabled and self.api_key is not None

# Global Sonar client instance
sonar_client = SonarClient()

async def get_sonar_client() -> SonarClient:
    """Get the global Sonar client instance"""
    return sonar_client 