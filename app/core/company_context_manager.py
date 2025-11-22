"""
Company Context Manager for Dynamic Company Profile Loading
Manages company-specific context throughout the application
"""

import logging
import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class CompanyContextManager:
    """Manages company-specific context for the configured company"""
    
    def __init__(self):
        self.company_profile = self._load_company_profile()
        self.setup_complete = self._check_setup_status()
    
    def _check_setup_status(self) -> bool:
        """Check if company profile has been configured"""
        try:
            # ALWAYS check actual company profile from database - no demo mode bypass
            # This ensures proper setup validation even in demo scenarios
            from app.database import QDRANT_CLIENT
            
            # Get all company profiles and check if any have setup_complete = True
            result = QDRANT_CLIENT.scroll(
                collection_name="company_profiles",
                limit=10
            )
            
            if result[0]:
                for profile in result[0]:
                    if profile.payload.get("setup_complete") == True:
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking setup status: {e}")
            return False
    
    def _load_company_profile(self) -> Dict[str, Any]:
        """Load the configured company profile"""
        try:
            # Check if demo mode is active
            if st.session_state.get("user_demo_mode", False):
                # Use demo profile manager to get demo company profile
                from app.components.demo_companies.demo_profile_manager import demo_profile_manager
                demo_company_id = demo_profile_manager.get_current_demo_company_id()
                if demo_company_id:
                    demo_company = demo_profile_manager.get_demo_company_profile(demo_company_id)
                    if demo_company:
                        logger.info(f"Using demo company profile: {demo_company.get('company_name')}")
                        return demo_company
            
            # Fall back to loading actual company profile from database
            from app.database import QDRANT_CLIENT
            
            # Get all company profiles and find the most recent one with setup_complete = True
            result = QDRANT_CLIENT.scroll(
                collection_name="company_profiles",
                limit=10
            )
            
            if result[0]:
                # Filter profiles with setup_complete = True
                completed_profiles = [
                    profile for profile in result[0] 
                    if profile.payload.get("setup_complete") == True
                ]
                
                if completed_profiles:
                    # Sort by setup_date (most recent first) and return the latest
                    completed_profiles.sort(
                        key=lambda p: p.payload.get("setup_date", ""), 
                        reverse=True
                    )
                    return completed_profiles[0].payload
            
            return self._get_default_company_profile()
        except Exception as e:
            logger.error(f"Error loading company profile: {e}")
            return self._get_default_company_profile()
    
    def _get_default_company_profile(self) -> Dict[str, Any]:
        """Get default company profile when none is configured - returns minimal empty profile"""
        return {
            "company_name": "",
            "core_business": "",
            "target_customers": [],
            "industries_served": [],
            "products": "",
            "value_propositions": "",
            "location": "",
            "company_size": "",
            "setup_complete": False
        }
    
    def get_company_name(self) -> str:
        """Get the configured company name"""
        return self.company_profile.get("company_name", "")
    
    def get_core_business(self) -> str:
        """Get the configured core business"""
        return self.company_profile.get("core_business", "")
    
    def get_target_customers(self) -> List[str]:
        """Get the configured target customers"""
        return self.company_profile.get("target_customers", [])
    
    def get_industries_served(self) -> List[str]:
        """Get the configured industries served"""
        return self.company_profile.get("industries_served", [])
    
    def get_products(self) -> str:
        """Get the configured products and services"""
        return self.company_profile.get("products", "")
    
    def get_value_propositions(self) -> str:
        """Get the configured value propositions"""
        return self.company_profile.get("value_propositions", "")
    
    def get_location(self) -> str:
        """Get the configured location"""
        return self.company_profile.get("location", "")
    
    def get_company_size(self) -> str:
        """Get the configured company size"""
        return self.company_profile.get("company_size", "Medium (51-200)")
    
    def get_primary_color(self) -> str:
        """Get the configured primary brand color"""
        return self.company_profile.get("primary_color", "#1f77b4")
    
    def get_logo_url(self) -> str:
        """Get the configured logo URL"""
        return self.company_profile.get("logo_url", "")
    
    def get_company_id(self) -> str:
        """Get the configured company ID"""
        return self.company_profile.get("company_id", "default")
    
    def is_setup_complete(self) -> bool:
        """Check if company setup is complete"""
        return self.setup_complete
    
    def get_company_context(self, context_type: str) -> Dict[str, Any]:
        """Get company-specific context for different use cases"""
        if context_type == "ai_prompts":
            return {
                "company_name": self.get_company_name(),
                "core_business": self.get_core_business(),
                "target_customers": self.get_target_customers(),
                "industries_served": self.get_industries_served(),
                "products": self.get_products(),
                "value_propositions": self.get_value_propositions()
            }
        elif context_type == "value_components":
            return {
                "company_name": self.get_company_name(),
                "core_business": self.get_core_business(),
                "target_customers": self.get_target_customers(),
                "industries_served": self.get_industries_served()
            }
        elif context_type == "persona_generation":
            return {
                "company_name": self.get_company_name(),
                "core_business": self.get_core_business(),
                "target_customers": self.get_target_customers(),
                "industries_served": self.get_industries_served(),
                "products": self.get_products()
            }
        else:
            return {
                "company_name": self.get_company_name(),
                "core_business": self.get_core_business(),
                "target_customers": self.get_target_customers(),
                "industries_served": self.get_industries_served(),
                "products": self.get_products(),
                "value_propositions": self.get_value_propositions(),
                "location": self.get_location(),
                "company_size": self.get_company_size()
            }
    
    def get_company_profile(self) -> Dict[str, Any]:
        """Get the complete company profile"""
        return self.company_profile
    
    def refresh_profile(self):
        """Refresh the company profile from database"""
        self.company_profile = self._load_company_profile()
        self.setup_complete = self._check_setup_status()
    
    def get_company_summary(self) -> str:
        """Get a formatted company summary for AI prompts"""
        context = self.get_company_context("ai_prompts")
        return f"""
        Company: {context['company_name']}
        Core Business: {context['core_business']}
        Target Customers: {', '.join(context['target_customers'])}
        Industries Served: {', '.join(context['industries_served'])}
        Products/Services: {context['products']}
        Value Propositions: {context['value_propositions']}
        """
    
    def get_company_basics(self) -> Dict[str, str]:
        """Get basic company information for forms and displays"""
        return {
            "name": self.get_company_name(),
            "core_business": self.get_core_business(),
            "location": self.get_location(),
            "company_size": self.get_company_size()
        }
    
    def get_industry_context(self) -> Dict[str, Any]:
        """Get industry-specific context"""
        return {
            "target_industries": self.get_industries_served(),
            "target_customers": self.get_target_customers(),
            "products": self.get_products()
        }
    
    def get_business_context(self, main_category: str, subcategory: str) -> Dict[str, Any]:
        """Get business context for specific categories"""
        return {
            "company_name": self.get_company_name(),
            "core_business": self.get_core_business(),
            "target_customers": self.get_target_customers(),
            "industries_served": self.get_industries_served(),
            "main_category": main_category,
            "subcategory": subcategory
        }
