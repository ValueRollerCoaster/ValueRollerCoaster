"""
Demo Populator
Populates value components with demo company data
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from .company_data import get_company_by_id, get_customers_for_company
from app.database import save_value_component, ensure_collections_exist
from app.categories import COMPONENT_STRUCTURES
import asyncio

logger = logging.getLogger(__name__)

class DemoPopulator:
    """Handles population of value components with demo company data"""
    
    def __init__(self):
        self.component_structures = COMPONENT_STRUCTURES
    
    async def populate_value_components(self, company_id: str, user_id: str, preserve_existing: bool = True) -> Dict[str, Any]:
        """
        Populate value components with demo company data
        
        Args:
            company_id: ID of the selected demo company
            user_id: User ID for saving components
            preserve_existing: Whether to preserve existing data
            
        Returns:
            Dict with success status and populated data
        """
        # Ensure collections and indexes exist before populating
        try:
            # ensure_collections_exist is async, so we need to await it
            await ensure_collections_exist()
            logger.info("Collections and indexes ensured before demo data population")
        except Exception as e:
            logger.warning(f"Could not ensure collections/indexes (continuing anyway): {e}")
        
        # Continue with population
        try:
            # Get company data
            company_data = get_company_by_id(company_id)
            if not company_data:
                return {"error": f"Company {company_id} not found"}
            
            # Get demo customers
            demo_customers = get_customers_for_company(company_id)
            
            # Generate value components based on company data (demo companies don't use website data)
            value_components = self._generate_value_components(company_data, use_website_data=False)
            
            # Save components to database
            saved_components = await self._save_components(value_components, user_id, preserve_existing)
            
            # Update session state
            self._update_session_state(value_components, demo_customers, company_data)
            
            return {
                "success": True,
                "components": value_components,
                "customers": demo_customers,
                "company": company_data,
                "saved_components": saved_components
            }
            
        except Exception as e:
            logger.error(f"Error populating demo data: {e}")
            return {"error": str(e)}
    
    def _generate_value_components(self, company_data: Dict[str, Any], use_website_data: bool = False) -> Dict[str, Any]:
        """Generate value components based on company data and optionally website content"""
        value_components = {}
        
        # Get company information
        company_name = company_data.get("company_name", "Demo Company")
        core_business = company_data.get("core_business", "Demo Business")
        products = company_data.get("products", "Demo Products")
        value_propositions = company_data.get("value_propositions", "Demo Value")
        target_customers = company_data.get("target_customers", [])
        industries_served = company_data.get("industries_served", [])
        
        # Only try to get website data for real companies, not demo companies
        website_context = self._get_website_context() if use_website_data else {}
        
        # Generate components for each main category
        for main_category, category_data in self.component_structures.items():
            value_components[main_category.lower()] = {}
            
            for subcategory, subcategory_data in category_data["subcategories"].items():
                value_components[main_category.lower()][subcategory.lower()] = {}
                
                for component in subcategory_data["items"]:
                    component_name = component["name"].lower()
                    
                    # Generate component value based on company data and website context
                    component_value = self._generate_component_value(
                        component_name, 
                        component["description"],
                        company_data,
                        main_category,
                        subcategory,
                        website_context
                    )
                    
                    value_components[main_category.lower()][subcategory.lower()][component_name] = component_value
        
        return value_components
    
    def _get_website_context(self) -> Dict[str, Any]:
        """Get website context for enhancing value components generation."""
        try:
            from app.database_company_website import get_company_website_data
            website_data = get_company_website_data()
            if website_data and website_data.get('content'):
                return website_data['content']
            return {}
        except Exception as e:
            logger.warning(f"Could not load website context: {e}")
            return {}
    
    def _generate_component_value(self, component_name: str, component_description: str, 
                                company_data: Dict[str, Any], main_category: str, subcategory: str, 
                                website_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a specific component value based on company data and website context"""
        
        # Get company information
        company_name = company_data.get("company_name", "Demo Company")
        core_business = company_data.get("core_business", "Demo Business")
        products = company_data.get("products", "Demo Products")
        value_propositions = company_data.get("value_propositions", "Demo Value")
        target_customers = company_data.get("target_customers", [])
        industries_served = company_data.get("industries_served", [])
        
        # Try to get relevant website content for this component
        website_value = self._extract_website_value_for_component(
            component_name, main_category, subcategory, website_context
        )
        
        # Generate value based on component type and company data
        if "quality" in component_name.lower():
            base_value = f"Premium quality standards for {company_name}'s {products.lower()}"
        elif "performance" in component_name.lower():
            base_value = f"High-performance solutions for {', '.join(target_customers)}"
        elif "innovation" in component_name.lower():
            base_value = f"Cutting-edge innovation in {', '.join(industries_served)}"
        elif "sustainability" in component_name.lower():
            base_value = f"Eco-friendly and sustainable {products.lower()}"
        elif "reliability" in component_name.lower():
            base_value = f"Reliable and dependable {products.lower()} for {', '.join(target_customers)}"
        elif "scalability" in component_name.lower():
            base_value = f"Scalable solutions for {', '.join(industries_served)}"
        elif "efficiency" in component_name.lower():
            base_value = f"Efficient processes for {core_business.lower()}"
        elif "support" in component_name.lower():
            base_value = f"Comprehensive support for {', '.join(target_customers)}"
        elif "training" in component_name.lower():
            base_value = f"Professional training for {', '.join(target_customers)}"
        elif "integration" in component_name.lower():
            base_value = f"Seamless integration with {', '.join(industries_served)}"
        elif "security" in component_name.lower():
            base_value = f"Advanced security for {products.lower()}"
        elif "compliance" in component_name.lower():
            base_value = f"Full compliance with industry standards for {', '.join(industries_served)}"
        else:
            # Generic value based on company data
            base_value = f"{value_propositions} for {', '.join(target_customers)} in {', '.join(industries_served)}"
        
        # Enhance with website content if available
        if website_value:
            return f"{base_value}. {website_value}"
        else:
            return base_value
    
    def _extract_website_value_for_component(self, component_name: str, main_category: str, 
                                           subcategory: str, website_context: Optional[Dict[str, Any]]) -> str:
        """Extract relevant website content for a specific component."""
        if not website_context:
            return ""
        
        # Map component types to website content categories with broader search
        content_mapping = {
            'quality': ['benefits', 'value_propositions', 'features', 'company_overview'],
            'performance': ['benefits', 'features', 'value_propositions', 'products_services'],
            'innovation': ['company_overview', 'features', 'value_propositions', 'about_us'],
            'sustainability': ['benefits', 'value_propositions', 'company_overview', 'about_us'],
            'reliability': ['benefits', 'value_propositions', 'features', 'products_services'],
            'scalability': ['features', 'benefits', 'value_propositions', 'products_services'],
            'efficiency': ['benefits', 'features', 'value_propositions', 'products_services'],
            'support': ['benefits', 'value_propositions', 'company_overview', 'about_us'],
            'training': ['benefits', 'value_propositions', 'company_overview', 'about_us'],
            'integration': ['features', 'benefits', 'value_propositions', 'products_services'],
            'security': ['features', 'benefits', 'value_propositions', 'products_services'],
            'compliance': ['benefits', 'value_propositions', 'company_overview', 'about_us']
        }
        
        # Get relevant content categories
        relevant_categories = content_mapping.get(component_name.lower(), ['benefits', 'value_propositions', 'features', 'company_overview'])
        
        # Extract content from relevant categories
        relevant_content = []
        for category in relevant_categories:
            content_items = website_context.get(category, [])
            if content_items:
                # Find content that mentions the component or related terms
                for item in content_items[:3]:  # Check first 3 items
                    item_lower = item.lower()
                    # More flexible matching - look for component name or related terms
                    if any(term in item_lower for term in [
                        component_name, 'quality', 'performance', 'benefit', 'feature', 
                        'advantage', 'value', 'capability', 'solution', 'technology',
                        'innovation', 'reliable', 'efficient', 'effective', 'superior'
                    ]):
                        relevant_content.append(item)
        
        # If no specific matches, try to get any content from the most relevant categories
        if not relevant_content:
            for category in relevant_categories[:2]:  # Try first 2 categories
                content_items = website_context.get(category, [])
                if content_items:
                    relevant_content.append(content_items[0])  # Take first item
                    break
        
        # Return the most relevant content (first match)
        if relevant_content:
            content = relevant_content[0]
            # Truncate if too long, but try to end at a sentence
            if len(content) > 200:
                truncated = content[:200]
                last_period = truncated.rfind('.')
                if last_period > 150:  # Only truncate at period if it's not too short
                    return truncated[:last_period + 1]
                else:
                    return truncated + "..."
            else:
                return content
        
        return ""
    
    async def _save_components(self, value_components: Dict[str, Any], user_id: str, preserve_existing: bool) -> List[Dict[str, Any]]:
        """Save value components to database"""
        saved_components = []
        
        for main_category, category_data in value_components.items():
            for subcategory, subcategory_data in category_data.items():
                for component_name, component_value in subcategory_data.items():
                    if component_value and component_value.strip():
                        try:
                            # Create component payload
                            payload = {
                                "main_category": main_category,
                                "category": subcategory,
                                "name": component_name,
                                "original_value": component_value,
                                "ai_processed_value": f"AI-generated benefit: {component_value}",
                                "chain_of_thought": f"Demo data generated for {component_name} based on company profile",
                                "weight": len(f"AI-generated benefit: {component_value}"),  # Calculate weight based on AI processed value length
                                "user_rating": 3,  # Set a meaningful rating for demo data
                                "user_id": user_id  # Ensure user_id is set
                            }
                            
                            # Save to database
                            success = save_value_component(payload)
                            if success:
                                saved_components.append(payload)
                                logger.info(f"Successfully saved demo component: {component_name} for {main_category}/{subcategory}")
                            else:
                                logger.error(f"Failed to save demo component: {component_name}")
                            
                        except Exception as e:
                            logger.error(f"Error saving component {component_name}: {e}")
        
        return saved_components
    
    def _update_session_state(self, value_components: Dict[str, Any], demo_customers: List[Dict[str, Any]], company_data: Dict[str, Any]):
        """Update session state with demo data"""
        # Update value components in session state
        if "value_components" not in st.session_state:
            st.session_state["value_components"] = {}
        
        # Debug: Log the value components being updated
        logger.warning(f"[demo_populator.py] Updating session state with {len(value_components)} main categories")
        for main_cat, cat_data in value_components.items():
            logger.warning(f"[demo_populator.py] Main category {main_cat}: {len(cat_data)} subcategories")
            for sub_cat, sub_data in cat_data.items():
                logger.warning(f"[demo_populator.py] Subcategory {sub_cat}: {len(sub_data)} components")
        
        st.session_state["value_components"].update(value_components)
        
        # Debug: Log the updated session state
        logger.warning(f"[demo_populator.py] Session state value_components now has {len(st.session_state['value_components'])} main categories")
        for main_cat, cat_data in st.session_state["value_components"].items():
            logger.warning(f"[demo_populator.py] Session state main category {main_cat}: {len(cat_data)} subcategories")
        
        # Update demo customers in session state
        st.session_state["demo_customers"] = demo_customers
        
        # Update selected demo company
        st.session_state["selected_demo_company"] = company_data
        
        # Mark demo data as populated
        st.session_state["demo_data_populated"] = True
        
        # Clear cache to ensure fresh data is loaded
        st.cache_data.clear()
        
        # Update AI processed values
        if "ai_processed_values" not in st.session_state:
            st.session_state["ai_processed_values"] = {}
        
        # Generate AI processed values for each component
        for main_category, category_data in value_components.items():
            if main_category not in st.session_state["ai_processed_values"]:
                st.session_state["ai_processed_values"][main_category] = {}
            
            for subcategory, subcategory_data in category_data.items():
                if subcategory not in st.session_state["ai_processed_values"][main_category]:
                    st.session_state["ai_processed_values"][main_category][subcategory] = {}
                
                for component_name, component_value in subcategory_data.items():
                    if component_value and component_value.strip():
                        st.session_state["ai_processed_values"][main_category][subcategory][component_name] = f"AI-generated benefit: {component_value}"
    
    def get_demo_customers_for_company(self, company_id: str) -> List[Dict[str, Any]]:
        """Get demo customers for a specific company"""
        return get_customers_for_company(company_id)
    
    def get_selected_demo_company(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected demo company"""
        return st.session_state.get("selected_demo_company")
    
    def is_demo_data_populated(self) -> bool:
        """Check if demo data has been populated"""
        return st.session_state.get("demo_data_populated", False)
