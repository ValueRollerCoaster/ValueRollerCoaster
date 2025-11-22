"""
Domain Company Lookup Utility
Provides domain-based company identification for verification.
"""

import logging
from typing import Dict, Optional, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_domain_from_url(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: Website URL
        
    Returns:
        Domain name (e.g., "example-online.com")
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        return domain
    except Exception as e:
        logger.error(f"Error extracting domain from URL {url}: {e}")
        return ""


async def lookup_company_by_domain(domain: str, pid: int = 0) -> Dict[str, Any]:
    """
    Lookup company information from domain using multiple sources.
    
    Args:
        domain: Domain name to lookup
        pid: Process ID for logging
        
    Returns:
        Dictionary with company information:
        {
            "company_name": str or None,
            "confidence": float (0.0-1.0),
            "source": str,
            "industry": Optional[str],
            "location": Optional[str],
            "error": Optional[str]
        }
    """
    if not domain:
        return {
            "company_name": None,
            "confidence": 0.0,
            "source": "none",
            "industry": None,
            "location": None,
            "error": "No domain provided"
        }
    
    logger.info(f"[PID {pid}] Looking up company for domain: {domain}")
    
    # Try Sonar domain validator first (most reliable)
    try:
        from app.ai.sonar.domain_validator import DomainValidator
        domain_validator = DomainValidator()
        
        domain_validation = await domain_validator.validate_domain_ownership(
            f"https://{domain}", None, pid
        )
        
        company_name = domain_validation.get("actual_company_name", "").strip()
        confidence = domain_validation.get("ownership_confidence", 0) / 10.0  # Convert to 0-1 scale
        company_business = domain_validation.get("company_business", "")
        
        if company_name and company_name.lower() not in ["unknown", "none", ""]:
            logger.info(f"[PID {pid}] Found company via Sonar: {company_name} (confidence: {confidence})")
            return {
                "company_name": company_name,
                "confidence": confidence,
                "source": "sonar_domain_validator",
                "industry": company_business if company_business and company_business.lower() != "unknown" else None,
                "location": None,
                "error": None
            }
    except Exception as e:
        logger.warning(f"[PID {pid}] Sonar domain lookup failed: {e}")
    
    # Fallback: Return domain-based suggestion (low confidence)
    # Extract potential company name from domain
    domain_parts = domain.replace('.com', '').replace('.de', '').replace('.net', '').replace('.org', '')
    domain_parts = domain_parts.replace('-', ' ').replace('_', ' ')
    # Capitalize first letter of each word
    suggested_name = ' '.join(word.capitalize() for word in domain_parts.split())
    
    logger.info(f"[PID {pid}] Using domain-based suggestion: {suggested_name} (low confidence)")
    return {
        "company_name": suggested_name if suggested_name else None,
        "confidence": 0.3,  # Low confidence for domain-based guess
        "source": "domain_parsing",
        "industry": None,
        "location": None,
        "error": "Unable to identify company from domain. Please verify manually."
    }

