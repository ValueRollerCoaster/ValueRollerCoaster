"""
Demo persona generation logic for fictional companies and customers.
This module handles persona generation specifically for demo mode scenarios.
"""

import logging
from typing import Dict, Any, Optional
from app.ai.demo_prompts import (
    DEMO_CONTEXT_PROMPT,
    DEMO_PERSONA_GENERATION_PROMPT,
    DEMO_MARKET_INTELLIGENCE_PROMPT,
    DEMO_WEBSITE_ANALYSIS_PROMPT,
    DEMO_CUSTOMER_PROFILE_PROMPT
)
from app.core.company_context_manager import CompanyContextManager
from app.database import fetch_all_value_components


class DemoPersonaGenerator:
    """Handles persona generation for demo scenarios."""
    
    def __init__(self):
        self.company_context = CompanyContextManager()
    
    def get_demo_context(self) -> str:
        """Get the demo context prompt to inform AI models about the demo nature."""
        return DEMO_CONTEXT_PROMPT
    
    def format_demo_persona_prompt(self, demo_customer: Dict[str, Any], user_id: str = "default_user") -> str:
        """Format the demo persona generation prompt with customer and company data."""
        try:
            # Get company profile
            company_profile = self.company_context.get_company_profile()
            
            # Get value components
            value_components = fetch_all_value_components(user_id=user_id)
            
            # Format value components for the prompt
            value_components_text = self._format_value_components(value_components)
            
            # Format the prompt
            prompt = DEMO_PERSONA_GENERATION_PROMPT.format(
                company_name=company_profile.get('company_name', 'Demo Company'),
                industry=company_profile.get('industry', 'Technology'),
                business_model=company_profile.get('business_model', 'B2B'),
                target_market=company_profile.get('target_market', 'Enterprise'),
                value_components=value_components_text
            )
            
            return prompt
            
        except Exception as e:
            logging.error(f"[DemoPersonaGenerator] Error formatting demo persona prompt: {e}")
            return DEMO_PERSONA_GENERATION_PROMPT.format(
                company_name="Demo Company",
                industry="Technology",
                business_model="B2B",
                target_market="Enterprise",
                value_components="Demo value components"
            )
    
    def format_demo_market_intelligence_prompt(self, user_id: str = "default_user") -> str:
        """Format the demo market intelligence prompt."""
        try:
            company_profile = self.company_context.get_company_profile()
            value_components = fetch_all_value_components(user_id=user_id)
            
            # Format value propositions
            value_propositions = self._format_value_components(value_components)
            
            prompt = DEMO_MARKET_INTELLIGENCE_PROMPT.format(
                company_name=company_profile.get('company_name', 'Demo Company'),
                industry=company_profile.get('industry', 'Technology'),
                business_model=company_profile.get('business_model', 'B2B'),
                value_propositions=value_propositions
            )
            
            return prompt
            
        except Exception as e:
            logging.error(f"[DemoPersonaGenerator] Error formatting market intelligence prompt: {e}")
            return DEMO_MARKET_INTELLIGENCE_PROMPT.format(
                company_name="Demo Company",
                industry="Technology",
                business_model="B2B",
                value_propositions="Demo value propositions"
            )
    
    def format_demo_website_analysis_prompt(self, website_url: str) -> str:
        """Format the demo website analysis prompt."""
        try:
            company_profile = self.company_context.get_company_profile()
            
            prompt = DEMO_WEBSITE_ANALYSIS_PROMPT.format(
                company_name=company_profile.get('company_name', 'Demo Company'),
                industry=company_profile.get('industry', 'Technology'),
                business_model=company_profile.get('business_model', 'B2B'),
                website_url=website_url
            )
            
            return prompt
            
        except Exception as e:
            logging.error(f"[DemoPersonaGenerator] Error formatting website analysis prompt: {e}")
            return DEMO_WEBSITE_ANALYSIS_PROMPT.format(
                company_name="Demo Company",
                industry="Technology",
                business_model="B2B",
                website_url=website_url
            )
    
    def format_demo_customer_profile_prompt(self, demo_customer: Dict[str, Any], user_id: str = "default_user") -> str:
        """Format the demo customer profile prompt."""
        try:
            company_profile = self.company_context.get_company_profile()
            value_components = fetch_all_value_components(user_id=user_id)
            
            # Format value propositions
            value_propositions = self._format_value_components(value_components)
            
            prompt = DEMO_CUSTOMER_PROFILE_PROMPT.format(
                customer_name=demo_customer.get('name', 'Demo Customer'),
                customer_industry=demo_customer.get('industry', 'Technology'),
                company_size=demo_customer.get('size', 'Medium'),
                location=demo_customer.get('location', 'Global'),
                description=demo_customer.get('description', 'Demo customer description'),
                vendor_company_name=company_profile.get('company_name', 'Demo Company'),
                vendor_industry=company_profile.get('industry', 'Technology'),
                vendor_value_propositions=value_propositions
            )
            
            return prompt
            
        except Exception as e:
            logging.error(f"[DemoPersonaGenerator] Error formatting customer profile prompt: {e}")
            return DEMO_CUSTOMER_PROFILE_PROMPT.format(
                customer_name="Demo Customer",
                customer_industry="Technology",
                company_size="Medium",
                location="Global",
                description="Demo customer description",
                vendor_company_name="Demo Company",
                vendor_industry="Technology",
                vendor_value_propositions="Demo value propositions"
            )
    
    def _format_value_components(self, value_components: Dict[str, Any]) -> str:
        """Format value components for use in prompts."""
        try:
            if not value_components:
                return "No value components available"
            
            formatted_components = []
            
            for category, subcategories in value_components.items():
                if isinstance(subcategories, dict):
                    category_components = []
                    for subcategory, components in subcategories.items():
                        if isinstance(components, list):
                            for component in components:
                                if isinstance(component, dict) and 'name' in component:
                                    category_components.append(component['name'])
                    
                    if category_components:
                        formatted_components.append(f"{category}: {', '.join(category_components)}")
            
            return "\n".join(formatted_components) if formatted_components else "No value components available"
            
        except Exception as e:
            logging.error(f"[DemoPersonaGenerator] Error formatting value components: {e}")
            return "Error formatting value components"
    
    def get_demo_persona_metadata(self, demo_customer: Dict[str, Any]) -> Dict[str, Any]:
        """Get metadata for demo persona generation."""
        return {
            "demo_mode": True,
            "demo_customer_id": demo_customer.get('id', 'unknown'),
            "demo_customer_name": demo_customer.get('name', 'Demo Customer'),
            "generation_context": "demo_fictional",
            "ai_prompts_used": "demo_specific"
        }
