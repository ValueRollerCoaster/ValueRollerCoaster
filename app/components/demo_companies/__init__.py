"""
Demo Companies System
Provides interactive demo company selection with funny scenarios
"""

from .company_data import DEMO_COMPANIES, get_company_by_id, get_customers_for_company
from .company_selector import render_company_selector
from .demo_populator import DemoPopulator
from .demo_integration import DemoIntegration

__all__ = [
    'DEMO_COMPANIES',
    'get_company_by_id', 
    'get_customers_for_company',
    'render_company_selector',
    'DemoPopulator',
    'DemoIntegration'
]
