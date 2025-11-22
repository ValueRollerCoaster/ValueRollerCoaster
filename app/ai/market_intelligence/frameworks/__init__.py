"""
Dynamic Industry Framework System
All frameworks are generated dynamically based on company profile and NACE system.
No hardcoded industry-specific frameworks - fully company-agnostic.
"""

from typing import Dict, Any
from .base_framework import BaseIndustryFramework
from .generic_framework import DynamicIndustryFramework

def get_framework(industry_name: str, company_profile: Dict[str, Any] = None) -> BaseIndustryFramework:
    """
    Get dynamic framework instance for given industry.
    Always uses DynamicIndustryFramework which adapts to company profile.
    
    Args:
        industry_name: Name of the industry
        company_profile: Company profile data for context (required for proper framework generation)
        
    Returns:
        DynamicIndustryFramework instance
    """
    # Always use dynamic framework - no hardcoded industry assumptions
    return DynamicIndustryFramework(industry_name, company_profile)

def get_available_frameworks() -> list:
    """
    Get list of available framework names.
    Since all frameworks are dynamic, this returns empty list.
    Framework is generated on-demand based on company profile.
    """
    return []  # No predefined frameworks - all are dynamic

__all__ = [
    'BaseIndustryFramework',
    'DynamicIndustryFramework',
    'get_framework',
    'get_available_frameworks'
] 