"""
Demo Integration
Integrates demo company system with existing application
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from .company_selector import render_company_selector
from .demo_populator import DemoPopulator
from .company_data import get_company_by_id, get_customers_for_company

logger = logging.getLogger(__name__)

class DemoIntegration:
    """Handles integration of demo company system with existing application"""
    
    def __init__(self):
        self.populator = DemoPopulator()
    
    async def render_demo_company_selector(self) -> Optional[str]:
        """
        Render the demo company selector and handle selection
        Returns the selected company ID or None
        """
        # Check if demo mode is enabled
        from app.config import ENABLE_DEMO_MODE
        if not ENABLE_DEMO_MODE:
            st.warning("Demo mode is not enabled. Please enable demo mode in the sidebar.")
            return None
        
        # Render company selector
        selected_company_id = render_company_selector()
        
        if selected_company_id:
            # Store selected company for button rendering elsewhere
            st.session_state.selected_demo_company_id = selected_company_id
            return selected_company_id
        
        return None
    
    def render_load_demo_button(self):
        """Render the Load Demo Data button separately"""
        if st.session_state.get("selected_demo_company_id"):
            if st.button("🎯 Load Demo", type="primary", help="Populate value components with selected company data"):
                return st.session_state.get("selected_demo_company_id")
        return None
    
    async def _handle_demo_data_loading(self, company_id: str):
        """Handle demo data loading for selected company"""
        try:
            # Use demo profile manager to get demo-specific user ID
            from app.components.demo_companies.demo_profile_manager import demo_profile_manager
            demo_user_id = demo_profile_manager.get_demo_user_id(company_id)
            
            # Show loading message
            with st.spinner(f"🎯 Loading demo data for {company_id}..."):
                # Populate demo data (always replace existing data)
                result = await self.populator.populate_value_components(
                    company_id, 
                    demo_user_id, 
                    preserve_existing=False
                )
                
                if result.get("success"):
                    # Switch to demo mode
                    from app.components.demo_companies.demo_profile_manager import demo_profile_manager
                    demo_profile_manager.switch_to_demo_mode(company_id)
                    
                    # Show success message
                    company_data = result.get("company", {})
                    company_name = company_data.get("company_name", "Demo Company")
                    
                    st.success(f"✅ Demo data loaded successfully for {company_name}!")
                    st.info(f"🎭 You can now generate personas with {len(result.get('customers', []))} demo customers")
                    
                    # Debug: Show what was loaded
                    components = result.get("components", {})
                    st.info(f"📊 Loaded {len(components)} main categories of value components")
                    for main_cat, cat_data in components.items():
                        st.info(f"   • {main_cat}: {len(cat_data)} subcategories")
                    
                    # Store demo customers in session state
                    st.session_state.demo_customers = result.get("customers", [])
                    
                    # Clear any existing persona
                    if "persona" in st.session_state:
                        del st.session_state["persona"]
                    
                    # Debug: Show session state after update
                    st.info(f"🔄 Session state now has {len(st.session_state.get('value_components', {}))} main categories")
                    
                    # Force refresh
                    st.rerun()
                else:
                    st.error(f"❌ Failed to load demo data: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"Error handling demo data loading: {e}")
            st.error(f"❌ Error loading demo data: {str(e)}")
    
    def get_demo_customers_for_persona_generation(self) -> List[Dict[str, Any]]:
        """Get demo customers for persona generation"""
        # Check session state first for demo customers
        demo_customers = st.session_state.get("demo_customers", [])
        if demo_customers:
            return demo_customers
        
        # Fallback to populator method
        if not self.populator.is_demo_data_populated():
            return []
        
        selected_company = self.populator.get_selected_demo_company()
        if not selected_company:
            return []
        
        company_id = selected_company.get("id")
        if not company_id:
            return []
        
        return get_customers_for_company(company_id)
    
    def is_demo_mode_active(self) -> bool:
        """Check if demo mode is active"""
        from app.config import ENABLE_DEMO_MODE
        return ENABLE_DEMO_MODE and self.populator.is_demo_data_populated()
    
    def get_demo_company_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the selected demo company"""
        return self.populator.get_selected_demo_company()
    
    def render_demo_customer_selector(self) -> Optional[Dict[str, Any]]:
        """Render demo customer selector for persona generation"""
        demo_customers = self.get_demo_customers_for_persona_generation()
        
        if not demo_customers:
            return None
        
        st.markdown("### 🎭 Demo Customers Available")
        st.markdown("Select a demo customer to generate a persona:")
        
        # Create customer options
        customer_options = []
        for i, customer in enumerate(demo_customers):
            option_text = f"{customer['company_name']} - {customer['description']}"
            customer_options.append((i, option_text, customer))
        
        # Create selector
        selected_index = st.selectbox(
            "Select Demo Customer:",
            range(len(customer_options)),
            format_func=lambda x: customer_options[x][1],
            help="Choose a demo customer to generate a persona"
        )
        
        if selected_index is not None:
            selected_customer = customer_options[selected_index][2]
            
            # Display customer preview
            st.markdown("---")
            st.markdown(f"**Selected Customer:** {selected_customer['company_name']}")
            st.markdown(f"**Industry:** {selected_customer['industry']}")
            st.markdown(f"**Size:** {selected_customer['size']}")
            st.markdown(f"**Location:** {selected_customer['location']}")
            st.markdown(f"**Description:** {selected_customer['description']}")
            
            return selected_customer
        
        return None
    
    def render_demo_mode_indicator(self):
        """Render demo mode indicator"""
        if self.is_demo_mode_active():
            selected_company = self.get_demo_company_info()
            if selected_company:
                company_name = selected_company.get("company_name", "Demo Company")
                st.info(f"🎭 **Demo Mode Active** - Using {company_name} data for value components and persona generation")
    
    def clear_demo_data(self):
        """Clear demo data from session state"""
        if "demo_customers" in st.session_state:
            del st.session_state["demo_customers"]
        if "selected_demo_company" in st.session_state:
            del st.session_state["selected_demo_company"]
        if "demo_data_populated" in st.session_state:
            del st.session_state["demo_data_populated"]
        
        st.success("✅ Demo data cleared successfully!")
        st.rerun()
    
