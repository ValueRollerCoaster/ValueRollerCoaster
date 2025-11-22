"""
Rate-Limited Gemini Client
Provides controlled parallelization while respecting Gemini API rate limits (10 RPM).
"""

import asyncio
import time
import logging
from typing import List, Any, Optional, cast
from app.ai.gemini_client import gemini_client

# Import deterministic configuration
try:
    from app.config import GEMINI_TEMPERATURE, GEMINI_MAX_TOKENS
except ImportError:
    # Fallback values if config import fails
    GEMINI_TEMPERATURE = 0.0
    GEMINI_MAX_TOKENS = 4000

logger = logging.getLogger(__name__)

class RateLimitedGeminiClient:
    """Gemini client with built-in rate limiting for controlled parallelization"""
    
    def __init__(self, max_rpm: int = 10, burst_limit: int = 3):
        """
        Initialize rate-limited client
        
        Args:
            max_rpm: Maximum requests per minute (default: 10 for Gemini)
            burst_limit: Maximum concurrent requests (default: 3 to be safe)
        """
        self.max_rpm = max_rpm
        self.burst_limit = burst_limit
        self.request_times = []
        self.semaphore = asyncio.Semaphore(burst_limit)
        self.lock = asyncio.Lock()
    
    async def rate_limited_call(self, prompt: str, temperature: Optional[float] = None, 
                               max_tokens: Optional[int] = None, model: Optional[str] = None, pid: int = 0) -> str:
        """
        Make a rate-limited Gemini API call with deterministic configuration
        
        Args:
            prompt: The prompt to send to Gemini
            temperature: Override temperature (uses config default if None)
            max_tokens: Override max tokens (uses config default if None)
            model: Model to use (defaults to configured model)
            pid: Process ID for logging (optional)
            
        Returns:
            Gemini response text
        """
        # Use deterministic defaults from config
        temperature = temperature if temperature is not None else GEMINI_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else GEMINI_MAX_TOKENS
        
        async with self.semaphore:
            # Wait for rate limit if necessary
            await self._wait_for_rate_limit()
            
            # Make the actual API call
            try:
                response = await gemini_client(prompt, temperature, max_tokens, model, pid=pid)
                
                # Check if gemini_client returned an error string (it doesn't raise exceptions, it returns error strings)
                if isinstance(response, str) and response.startswith("ERROR:"):
                    # If it's a 503 error, we might want to retry at this level too
                    # But gemini_client already has retry logic, so if we get here, all retries failed
                    error_msg = response
                    logger.error(f"Rate-limited Gemini call returned error: {error_msg[:200]}")
                    # Return the error string so caller can handle it
                    return response
                
                # Record this request time only on success
                async with self.lock:
                    self.request_times.append(time.time())
                
                return response
                
            except Exception as e:
                logger.error(f"Rate-limited Gemini call failed with exception: {e}")
                raise
    
    async def _wait_for_rate_limit(self):
        """Wait if we've hit the rate limit"""
        async with self.lock:
            current_time = time.time()
            
            # Remove requests older than 1 minute
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            # If we've hit the limit, wait
            if len(self.request_times) >= self.max_rpm:
                # Calculate wait time (wait until the oldest request is 1 minute old)
                oldest_request = min(self.request_times)
                wait_time = 60 - (current_time - oldest_request)
                
                if wait_time > 0:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
    
    async def batch_call(self, prompts: List[str], temperatures: Optional[List[float]] = None, 
                        max_tokens_list: Optional[List[int]] = None) -> List[str]:
        """
        Make multiple API calls in parallel with rate limiting and deterministic configuration
        
        Args:
            prompts: List of prompts to send
            temperatures: List of temperatures (defaults to config default for all)
            max_tokens_list: List of max tokens (defaults to config default for all)
            
        Returns:
            List of responses in same order as prompts (exceptions are converted to error strings)
        """
        if temperatures is None:
            temperatures = [GEMINI_TEMPERATURE] * len(prompts)
        if max_tokens_list is None:
            max_tokens_list = [GEMINI_MAX_TOKENS] * len(prompts)
        
        # Create tasks for all calls
        tasks = [
            self.rate_limited_call(prompt, temp, max_tokens)
            for prompt, temp, max_tokens in zip(prompts, temperatures, max_tokens_list)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error strings to match return type
        # Type narrowing: results is List[str | BaseException], we convert to List[str]
        processed_results = [
            str(result) if isinstance(result, Exception) else cast(str, result)
            for result in results
        ]
        return cast(List[str], processed_results)
    
    def get_current_rate(self) -> float:
        """Get current requests per minute"""
        current_time = time.time()
        recent_requests = [t for t in self.request_times if current_time - t < 60]
        return len(recent_requests)
    
    def get_queue_status(self) -> dict:
        """Get current queue and rate limiting status"""
        return {
            "current_rate": self.get_current_rate(),
            "max_rpm": self.max_rpm,
            "burst_limit": self.burst_limit,
            "queue_size": len(self.request_times)
        }

# Global instance for easy access
rate_limited_gemini = RateLimitedGeminiClient() 