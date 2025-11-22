"""
Demo Data Integration System
Integrates generated demo data with the actual value components system
"""

import streamlit as st
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DemoDataIntegrator:
    """Integrates demo data with the value components system"""
    
    def __init__(self):
        self.company_context = None
        self._load_company_context()
    
    def _load_company_context(self):
        """Load company context for demo generation"""
        try:
            from app.core.company_context_manager import CompanyContextManager
            self.company_context = CompanyContextManager()
        except Exception as e:
            logger.error(f"Error loading company context: {e}")
            self.company_context = None
    
    async def populate_value_components(self, user_id: str, preserve_existing: bool = True) -> Dict[str, Any]:
        """Populate value components with demo data based on company profile"""
        try:
            from app.utils.demo_function import demo_generator
            from app.database import save_value_component
            from app.ai.gemini_client import gemini_client
            
            # Generate demo components
            components_result = await demo_generator.generate_demo_value_components(user_id)
            
            if not components_result.get("success"):
                return {"error": "Failed to generate demo components"}
            
            components = components_result.get("components", {})
            saved_components = []
            
            # Process each category
            for main_category, subcategories in components.items():
                for subcategory, items in subcategories.items():
                    for item in items:
                        # Generate AI customer benefit
                        customer_benefit = await self._generate_customer_benefit(
                            item, main_category, subcategory
                        )
                        
                        # Create value component structure
                        component_data = {
                            "main_category": main_category,
                            "category": subcategory,
                            "name": item,
                            "original_value": item,
                            "ai_benefit": customer_benefit,
                            "user_id": user_id,
                            "created_at": datetime.now().isoformat(),
                            "is_demo": True
                        }
                        
                        # Save to database
                        success = save_value_component(component_data)
                        if success:
                            saved_components.append(component_data)
            
            return {
                "success": True,
                "components_saved": len(saved_components),
                "components": saved_components
            }
            
        except Exception as e:
            logger.error(f"Error populating value components: {e}")
            return {"error": str(e)}
    
    async def _generate_customer_benefit(self, component: str, main_category: str, subcategory: str) -> str:
        """Generate customer benefit for a value component using AI"""
        try:
            from app.ai.gemini_client import gemini_client
            
            if not self.company_context:
                return f"Customer benefit for {component}"
            
            # Get company context
            company_name = self.company_context.get_company_name()
            core_business = self.company_context.get_core_business()
            target_customers = self.company_context.get_target_customers()
            
            prompt = f"""
            Generate a customer benefit statement for this value component:
            
            COMPANY: {company_name}
            CORE BUSINESS: {core_business}
            TARGET CUSTOMERS: {', '.join(target_customers)}
            
            VALUE COMPONENT:
            - Component: {component}
            - Category: {main_category} > {subcategory}
            
            Generate a 1-2 sentence customer benefit that explains how this component provides value to the target customers. Focus on:
            - Specific business outcomes
            - Measurable benefits
            - Customer pain points addressed
            - Competitive advantages
            
            Keep it concise and business-focused.
            """
            
            response = await gemini_client(prompt, temperature=0.3, max_tokens=200)
            return response if response else f"Customer benefit for {component}"
            
        except Exception as e:
            logger.error(f"Error generating customer benefit: {e}")
            return f"Customer benefit for {component}"
    
    async def populate_demo_customers(self, user_id: str) -> Dict[str, Any]:
        """Populate demo customers for persona generation"""
        try:
            from app.utils.demo_function import demo_generator
            
            # Generate demo customers
            customers_result = await demo_generator.generate_demo_customers(user_id)
            
            if not customers_result.get("success"):
                return {"error": "Failed to generate demo customers"}
            
            customers = customers_result.get("customers", [])
            
            # Add IDs to customers and store in session state
            for i, customer in enumerate(customers):
                customer["id"] = f"customer_{i+1}"
            
            st.session_state.demo_customers = customers
            st.session_state.demo_customers_available = True
            
            return {
                "success": True,
                "customers": customers,
                "count": len(customers)
            }
            
        except Exception as e:
            logger.error(f"Error populating demo customers: {e}")
            return {"error": str(e)}
    
    async def get_demo_customer_websites(self) -> List[str]:
        """Get demo customer websites for persona generation"""
        try:
            customers = st.session_state.get("demo_customers", [])
            websites = [customer.get("website", "") for customer in customers if customer.get("website")]
            return websites
        except Exception as e:
            logger.error(f"Error getting demo customer websites: {e}")
            return []
    
    def get_demo_customer_info(self, website: str) -> Dict[str, Any]:
        """Get demo customer info for a specific website"""
        try:
            customers = st.session_state.get("demo_customers", [])
            for customer in customers:
                if customer.get("website") == website:
                    return customer
            return {}
        except Exception as e:
            logger.error(f"Error getting demo customer info: {e}")
            return {}

# Global integrator instance
demo_integrator = DemoDataIntegrator()

async def populate_demo_data(user_id: str, preserve_existing: bool = True) -> Dict[str, Any]:
    """Main function to populate demo data"""
    try:
        # Populate value components
        components_result = await demo_integrator.populate_value_components(user_id, preserve_existing)
        
        # Populate demo customers
        customers_result = await demo_integrator.populate_demo_customers(user_id)
        
        return {
            "success": True,
            "components": components_result,
            "customers": customers_result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error populating demo data: {e}")
        return {"error": str(e)}

def update_session_state(components: Dict[str, Any], customers: Dict[str, Any]):
    """Update session state with demo data"""
    try:
        # Update session state for demo data
        st.session_state.demo_data_populated = True
        st.session_state.demo_components = components
        st.session_state.demo_customers = customers
        st.session_state.demo_timestamp = datetime.now().isoformat()
        
        logger.info("Demo data session state updated successfully")
    except Exception as e:
        logger.error(f"Error updating session state: {e}")

# Legacy function for backward compatibility
demo_function = type('DemoFunction', (), {
    'populate_demo_data': populate_demo_data,
    'update_session_state': update_session_state
})()
