"""
Components for AI Framework view
"""

from .overview_dashboard import render_overview_dashboard
from .industry_frameworks import render_industry_frameworks
from .framework_properties import render_framework_properties
from .company_context import render_company_context
from .prompt_flow import render_prompt_flow
from .nace_integration import render_nace_integration

__all__ = [
    'render_overview_dashboard',
    'render_industry_frameworks',
    'render_framework_properties',
    'render_company_context',
    'render_prompt_flow',
    'render_nace_integration'
]

