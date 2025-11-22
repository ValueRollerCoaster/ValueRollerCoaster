"""
Demo Company Profile Manager
Manages demo company profiles and data isolation from real company data.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from app.database import fetch_all_value_components, save_value_component, delete_all_value_components
from app.components.demo_companies.company_data import DEMO_COMPANIES

logger = logging.getLogger(__name__)

class DemoProfileManager:
    """Manages demo company profiles and data isolation."""
    
    def __init__(self):
        self.demo_user_prefix = "demo_user_"
    
    def get_demo_user_id(self, demo_company_id: str) -> str:
        """Get demo-specific user ID for a demo company, isolated per authenticated user."""
        # Get the real authenticated user_id to ensure data isolation
        real_user_id = st.session_state.get("user_id", "anonymous")
        # Format: demo_user_{real_user_id}_{demo_company_id}
        # This ensures each authenticated user has their own isolated demo data
        return f"{self.demo_user_prefix}{real_user_id}_{demo_company_id}"
    
    def is_demo_user_id(self, user_id: str) -> bool:
        """Check if a user ID is a demo user ID."""
        return user_id.startswith(self.demo_user_prefix)
    
    def get_demo_company_id_from_user_id(self, user_id: str) -> Optional[str]:
        """Get demo company ID from demo user ID."""
        if self.is_demo_user_id(user_id):
            # Format: demo_user_{real_user_id}_{demo_company_id}
            # Remove prefix to get: {real_user_id}_{demo_company_id}
            without_prefix = user_id.replace(self.demo_user_prefix, "")
            # Split by last underscore to get demo_company_id (handles cases where user_id contains underscores)
            parts = without_prefix.rsplit("_", 1)
            if len(parts) == 2:
                return parts[1]  # Return the demo_company_id (last part)
            # Fallback for old format: demo_user_{demo_company_id} (backward compatibility)
            return without_prefix
        return None
    
    def get_current_demo_company_id(self) -> Optional[str]:
        """Get currently active demo company ID from session state."""
        return st.session_state.get("selected_demo_company_id")
    
    def get_current_user_id(self) -> str:
        """Get current user ID, switching between demo and real based on demo mode."""
        demo_mode_active = st.session_state.get("user_demo_mode", False)
        
        if demo_mode_active:
            demo_company_id = self.get_current_demo_company_id()
            if demo_company_id:
                demo_user_id = self.get_demo_user_id(demo_company_id)
                logging.warning(f"[demo_profile_manager] Demo mode active, using demo_user_id={demo_user_id}")
                return demo_user_id
        
        # Return real user ID
        real_user_id = st.session_state.get("user_id", "default_user")
        logging.warning(f"[demo_profile_manager] Real mode, using real_user_id={real_user_id}")
        return real_user_id
    
    def get_demo_company_profile(self, demo_company_id: str) -> Dict[str, Any]:
        """Get demo company profile data."""
        return DEMO_COMPANIES.get(demo_company_id, {})
    
    def is_demo_mode_active(self) -> bool:
        """Check if demo mode is currently active."""
        return st.session_state.get("user_demo_mode", False)
    
    def switch_to_demo_mode(self, demo_company_id: str):
        """Switch to demo mode with specific demo company."""
        st.session_state.user_demo_mode = True
        st.session_state.selected_demo_company_id = demo_company_id
        logger.info(f"Switched to demo mode for company: {demo_company_id}")
    
    def switch_to_real_mode(self):
        """Switch to real company mode."""
        st.session_state.user_demo_mode = False
        if "selected_demo_company_id" in st.session_state:
            del st.session_state.selected_demo_company_id
        logger.info("Switched to real company mode")
    
    async def populate_demo_company_data(self, demo_company_id: str, user_id: str = None) -> Dict[str, Any]:
        """Populate demo company data for a specific demo company."""
        try:
            if user_id is None:
                user_id = self.get_demo_user_id(demo_company_id)
            
            # Get demo company profile
            demo_company = self.get_demo_company_profile(demo_company_id)
            if not demo_company:
                return {"success": False, "error": f"Demo company {demo_company_id} not found"}
            
            # Import demo populator
            from app.components.demo_companies.demo_populator import DemoPopulator
            populator = DemoPopulator()
            
            # Populate value components for this demo company
            result = await populator.populate_value_components(
                demo_company_id, 
                user_id, 
                preserve_existing=False
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error populating demo company data: {e}")
            return {"success": False, "error": str(e)}
    
    async def clear_demo_company_data(self, demo_company_id: str) -> Dict[str, Any]:
        """Clear all data for a specific demo company."""
        try:
            demo_user_id = self.get_demo_user_id(demo_company_id)
            
            # Delete all value components for this demo company
            success = delete_all_value_components(demo_user_id)
            
            if success:
                # Clear session state for this demo company
                if st.session_state.get("selected_demo_company_id") == demo_company_id:
                    # Clear demo-related session state
                    if "demo_customers" in st.session_state:
                        del st.session_state["demo_customers"]
                    if "selected_demo_company" in st.session_state:
                        del st.session_state["selected_demo_company"]
                    if "demo_data_populated" in st.session_state:
                        del st.session_state["demo_data_populated"]
                    if "value_components" in st.session_state:
                        del st.session_state["value_components"]
                    if "ai_processed_values" in st.session_state:
                        del st.session_state["ai_processed_values"]
                
                return {"success": True, "message": "Demo company data cleared successfully"}
            else:
                return {"success": False, "error": "Failed to clear demo company data"}
                
        except Exception as e:
            logger.error(f"Error clearing demo company data: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_demo_company_value_components(self, demo_company_id: str) -> Dict[str, Any]:
        """Get value components for a specific demo company."""
        try:
            demo_user_id = self.get_demo_user_id(demo_company_id)
            return await fetch_all_value_components(user_id=demo_user_id)
        except Exception as e:
            logger.error(f"Error getting demo company value components: {e}")
            return {}
    
    def get_available_demo_companies(self) -> List[Dict[str, Any]]:
        """Get list of available demo companies."""
        companies = []
        for company_id, company_data in DEMO_COMPANIES.items():
            companies.append({
                "id": company_id,
                "name": company_data.get("company_name", "Unknown"),
                "description": company_data.get("core_business", ""),
                "industry": company_data.get("industries_served", [""])[0] if company_data.get("industries_served") else "Unknown"
            })
        return companies
    
    def validate_demo_company_id(self, demo_company_id: str) -> bool:
        """Validate if demo company ID exists."""
        return demo_company_id in DEMO_COMPANIES
    
    def get_demo_company_summary(self, demo_company_id: str) -> Dict[str, Any]:
        """Get summary information for a demo company."""
        company_data = self.get_demo_company_profile(demo_company_id)
        if not company_data:
            return {}
        
        return {
            "id": demo_company_id,
            "name": company_data.get("company_name", "Unknown"),
            "industry": company_data.get("industries_served", [""])[0] if company_data.get("industries_served") else "Unknown",
            "size": company_data.get("company_size", "Unknown"),
            "location": company_data.get("location", "Unknown"),
            "description": company_data.get("core_business", ""),
            "demo_customers_count": len(company_data.get("demo_customers", []))
        }

# Global instance
demo_profile_manager = DemoProfileManager()
