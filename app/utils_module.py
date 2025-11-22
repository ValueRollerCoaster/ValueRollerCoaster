import logging
import os
import json
import time
import functools
from typing import Optional, Dict, Any, List, Callable
from urllib.parse import urlparse
from app.config import (
    MAX_URL_LENGTH,
    MAX_ANALYSIS_SIZE,
    MAX_VALUE_BRICKS,
    CACHE_TTL,
    MAX_CACHE_SIZE,
    RETRY_DELAY,
    MAX_RETRIES,
    LOG_FORMAT,
    LOG_LEVEL
)
import requests
from app.core.company_context_manager import CompanyContextManager

logger = logging.getLogger(__name__)
_cache: Dict[str, Dict[str, Any]] = {}

def validate_inputs(website: str, product: str, bom_cost: float, offer_price: float) -> bool:
    try:
        if not website or not is_valid_url(website):
            return False
        if not product or len(product.strip()) < 2:
            return False
        if bom_cost <= 0 or offer_price <= 0 or bom_cost >= offer_price:
            return False
        return True
    except Exception as e:
        logger.error(f"Error in validate_inputs: {str(e)}")
        return False

def is_valid_url(url: str) -> bool:
    """Validate if URL is properly formatted"""
    if not url or not isinstance(url, str):
        return False
    try:
        url = url.strip()  # Remove leading/trailing whitespace
        if not url:  # Empty after stripping
            return False
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def validate_url(url: str) -> bool:
    try:
        if len(url) > MAX_URL_LENGTH:
            return False
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"URL validation error: {str(e)}")
        return False

def validate_analysis_size(analysis: dict, max_size: int = 100000) -> bool:
    size = len(json.dumps(analysis).encode('utf-8'))
    return size <= max_size

def validate_value_bricks(bricks: List[Dict[str, Any]]) -> bool:
    try:
        if len(bricks) > MAX_VALUE_BRICKS:
            return False
        for brick in bricks:
            if not all(k in brick for k in ['name', 'value', 'description']):
                return False
            if not isinstance(brick['value'], (int, float)):
                return False
            if not 0 <= brick['value'] <= 100:
                return False
        return True
    except Exception as e:
        logger.error(f"Value bricks validation error: {str(e)}")
        return False

def safe_truncate_text(text: str, max_length: int) -> str:
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space != -1:
        return truncated[:last_space] + "..."
    return truncated + "..."

def cache_result(ttl: int = CACHE_TTL):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            if key in _cache:
                cache_data = _cache[key]
                if time.time() - cache_data['timestamp'] < ttl:
                    return cache_data['result']
            result = func(*args, **kwargs)
            _cache[key] = {
                'result': result,
                'timestamp': time.time()
            }
            if len(_cache) > MAX_CACHE_SIZE:
                oldest_key = min(_cache.keys(), key=lambda k: _cache[k]['timestamp'])
                del _cache[oldest_key]
            return result
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = MAX_RETRIES, delay: int = RETRY_DELAY):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Retry {attempt+1}/{max_retries} for {func.__name__} due to error: {e}")
                    time.sleep(delay)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def safe_json_loads(data: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(data)
    except Exception as e:
        logger.error(f"safe_json_loads error: {str(e)}")
        return None

def safe_json_dumps(data: Dict[str, Any]) -> Optional[str]:
    try:
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        logger.error(f"safe_json_dumps error: {str(e)}")
        return None

def format_currency(value: float) -> str:
    try:
        return f"${value:,.2f}"
    except Exception:
        return str(value)

def safe_str(val):
    try:
        return str(val)
    except Exception:
        return ""

def flatten_and_stringify(items):
    if isinstance(items, dict):
        return ", ".join(f"{k}: {v}" for k, v in items.items())
    elif isinstance(items, list):
        return ", ".join(str(i) for i in items)
    else:
        return str(items)

def get_relevance_keywords():
    keywords = set()
    company_context = CompanyContextManager()
    company_profile = company_context.get_company_profile()
    
    # Add product categories and features
    for prod in company_profile.get("products", []):
        if isinstance(prod, dict):
            keywords.add(prod.get("category", "").lower())
            keywords.update([f.lower() for f in prod.get("features", [])])
        else:
            keywords.add(str(prod).lower())
    
    # Add industries served
    keywords.update([industry.lower() for industry in company_profile.get("industries_served", [])])
    
    # Add core business terms
    core_business = company_profile.get("core_business", "")
    if core_business:
        keywords.update([w.lower() for w in core_business.split()])
    
    return keywords

def is_potential_customer_website(url):
    """
    Checks if the target website is likely to be a business that could use our products,
    based on keywords from our company profile (products, features, industries, core business).
    Returns True if relevant, False otherwise.
    """
    keywords = get_relevance_keywords()
    try:
        resp = requests.get(url, timeout=5)
        content = resp.text.lower()
        # Check if any of your product/industry keywords appear in the website
        return any(kw in content for kw in keywords)
    except Exception:
        return False 