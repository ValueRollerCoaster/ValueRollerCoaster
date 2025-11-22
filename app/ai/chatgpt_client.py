import os
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Import deterministic configuration
try:
    from app.config import (
        CHATGPT_TEMPERATURE, CHATGPT_SEED, CHATGPT_TOP_P, 
        CHATGPT_MAX_TOKENS
    )
except ImportError:
    # Fallback values if config import fails
    CHATGPT_TEMPERATURE = 0.0
    CHATGPT_SEED = 42
    CHATGPT_TOP_P = 1.0
    CHATGPT_MAX_TOKENS = 4000

# Import from config to get the API key
try:
    from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
except ImportError:
    # Fallback to environment variables if config import fails
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Create dedicated ChatGPT logger
def setup_chatgpt_logger():
    """Setup dedicated logger for ChatGPT activities"""
    chatgpt_logger = logging.getLogger('chatgpt_model')
    chatgpt_logger.setLevel(logging.INFO)
    
    # Create file handler for ChatGPT-specific log file
    log_file = os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'chatgpt_model.log')
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '[%(asctime)s] [PID %(process)d] [%(levelname)s] [%(funcName)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    chatgpt_logger.addHandler(file_handler)
    
    return chatgpt_logger

# Initialize ChatGPT logger
chatgpt_logger = setup_chatgpt_logger()
logger = logging.getLogger(__name__)

class ChatGPTClient:
    """ChatGPT client with web search capabilities for enhanced persona generation"""
    
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        self.base_url = OPENAI_BASE_URL
        
        if not self.api_key:
            logger.error("[chatgpt_client] OPENAI_API_KEY environment variable not set.")
            raise ValueError("OPENAI_API_KEY environment variable not set.")
    
    async def generate_response(self, prompt: str, temperature: Optional[float] = None, 
                               max_tokens: Optional[int] = None, system_message: Optional[str] = None,
                               use_web_search: bool = False, pid: int = 0) -> str:
        """
        Generate response using ChatGPT with deterministic configuration for consistent results.
        
        Args:
            prompt: The user prompt
            temperature: Override temperature (uses config default if None)
            max_tokens: Override max tokens (uses config default if None)
            system_message: Optional system message
            use_web_search: Whether to enable web search grounding
            pid: Process ID for logging
        """
        start_time = datetime.now()
        
        # Use deterministic defaults from config
        temperature = float(temperature if temperature is not None else CHATGPT_TEMPERATURE)
        max_tokens = int(max_tokens if max_tokens is not None else CHATGPT_MAX_TOKENS)
        
        chatgpt_logger.info(f"[PID {pid}] [generate_response] START - Model: {self.model}, Temp: {temperature}, MaxTokens: {max_tokens}, Seed: {CHATGPT_SEED}, WebSearch: {use_web_search}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare messages
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add web search tool if requested
            tools = None
            if use_web_search:
                # Since web search API has format issues, we'll enhance the prompt to request current information
                # and use the model's knowledge up to its training cutoff
                enhanced_prompt = f"{prompt}\n\nIMPORTANT: Please provide the most current and up-to-date information available to you. If you're asked about recent events, trends, or developments, focus on the most recent information you have access to."
                prompt = enhanced_prompt
            
            messages.append({"role": "user", "content": prompt})
            
            # Build payload with deterministic parameters (ChatGPT only supports temperature, max_tokens, top_p, and seed)
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": CHATGPT_TOP_P
            }
            
            # Add seed if supported by the model
            if CHATGPT_SEED is not None:
                payload["seed"] = CHATGPT_SEED
            
            if tools:
                payload["tools"] = tools
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract the response text
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        response_text = choice["message"]["content"]
                        if response_text is None:
                            chatgpt_logger.error(f"[PID {pid}] [generate_response] ERROR - Response content is None")
                            return "ERROR: Response content is None"
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        
                        # Extract token usage if available
                        token_usage = {}
                        if "usage" in data:
                            usage = data["usage"]
                            token_usage = {
                                "prompt_tokens": usage.get("prompt_tokens", 0),
                                "completion_tokens": usage.get("completion_tokens", 0),
                                "total_tokens": usage.get("total_tokens", 0)
                            }
                            chatgpt_logger.info(f"[PID {pid}] [generate_response] SUCCESS - Duration: {duration:.2f}s, ResponseLength: {len(response_text)} chars, Tokens: {token_usage.get('total_tokens', 0)} (Prompt: {token_usage.get('prompt_tokens', 0)}, Completion: {token_usage.get('completion_tokens', 0)})")
                        else:
                            chatgpt_logger.info(f"[PID {pid}] [generate_response] SUCCESS - Duration: {duration:.2f}s, ResponseLength: {len(response_text)} chars")
                        
                        return response_text
                    else:
                        chatgpt_logger.error(f"[PID {pid}] [generate_response] ERROR - Unexpected response structure: {data}")
                        return f"ERROR: Unexpected response structure"
                else:
                    chatgpt_logger.error(f"[PID {pid}] [generate_response] ERROR - No choices in response: {data}")
                    return f"ERROR: No choices in response"
                    
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}: {e.response.text[:500] if e.response.text else 'No response body'}"
            chatgpt_logger.error(f"[PID {pid}] [generate_response] HTTP_ERROR - Status: {e.response.status_code}, Response: {error_detail}")
            return f"ERROR: {error_detail}"
        except httpx.TimeoutException as e:
            error_detail = f"Request timeout after 120 seconds"
            chatgpt_logger.error(f"[PID {pid}] [generate_response] TIMEOUT_ERROR - {error_detail}")
            return f"ERROR: {error_detail}"
        except Exception as e:
            error_detail = str(e) if str(e) else f"{type(e).__name__} (no message)"
            chatgpt_logger.error(f"[PID {pid}] [generate_response] UNEXPECTED_ERROR - {type(e).__name__}: {error_detail}")
            chatgpt_logger.error(f"[PID {pid}] [generate_response] Exception details: {repr(e)}")
            return f"ERROR: {error_detail}"
    
    async def generate_with_web_search(self, prompt: str, temperature: Optional[float] = None, 
                                      max_tokens: Optional[int] = None, pid: int = 0) -> str:
        """Convenience method for generating responses with web search enabled."""
        chatgpt_logger.info(f"[PID {pid}] [generate_with_web_search] START - Web search enabled")
        return await self.generate_response(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            use_web_search=True,
            pid=pid
        )
    
    def get_grounded_company_summary(self, website_url: str, pid: int = 0) -> str:
        """
        Uses ChatGPT with web search to fetch and summarize up-to-date company information.
        Returns a concise, factual summary for the given website URL.
        """
        try:
            chatgpt_logger.info(f"[PID {pid}] [get_grounded_company_summary] START - Website: {website_url}")
            
            prompt = (
                f"Summarize the business, products, and value proposition of the company that owns and operates the website at {website_url}. "
                "Focus ONLY on the company that controls this specific domain. "
                "Do not analyze any other companies mentioned in search results. "
                "Use up-to-date information from the web. Be concise and factual. "
                "Start by clearly identifying the company name and confirming it owns this website."
            )
            
            # For now, return a placeholder since web search has API issues
            # This can be fixed later when web search is properly implemented
            chatgpt_logger.info(f"[PID {pid}] [get_grounded_company_summary] SUCCESS - Using placeholder response")
            return f"Company summary for {website_url}: [Placeholder - Web search functionality to be implemented]"
            
        except Exception as e:
            chatgpt_logger.error(f"[PID {pid}] [get_grounded_company_summary] ERROR - {e}")
            return f"ERROR: {e}"

# Global instance for compatibility with existing code (lazy initialization)
_chatgpt_client_instance = None

def get_chatgpt_client():
    """Get or create ChatGPT client instance with lazy initialization."""
    global _chatgpt_client_instance
    if _chatgpt_client_instance is None:
        try:
            _chatgpt_client_instance = ChatGPTClient()
        except ValueError as e:
            # If API key is not set, create a dummy client that returns error messages
            class DummyChatGPTClient:
                async def generate_response(self, prompt: str, temperature: Optional[float] = None, 
                                           max_tokens: Optional[int] = None, system_message: Optional[str] = None,
                                           use_web_search: bool = False, pid: int = 0) -> str:
                    return f"ERROR: {str(e)}"
                
                async def generate_with_web_search(self, prompt: str, temperature: Optional[float] = None, 
                                                  max_tokens: Optional[int] = None, pid: int = 0) -> str:
                    return f"ERROR: {str(e)}"
                
                def get_grounded_company_summary(self, website_url: str, pid: int = 0) -> str:
                    return f"ERROR: {str(e)}"
            
            _chatgpt_client_instance = DummyChatGPTClient()
    
    return _chatgpt_client_instance

async def chatgpt_generate(prompt: str, temperature: Optional[float] = None, 
                          max_tokens: Optional[int] = None, use_web_search: bool = False, pid: int = 0) -> str:
    """Convenience function for generating ChatGPT responses with deterministic configuration."""
    client = get_chatgpt_client()
    return await client.generate_response(
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        use_web_search=use_web_search,
        pid=pid
    ) 