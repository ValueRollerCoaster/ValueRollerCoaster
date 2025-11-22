"""
Company Setup Wizard for One-Time Company Configuration
Allows companies to configure their profile when first deploying the app
"""

import streamlit as st
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class CompanySetupWizard:
    """Handles one-time company profile setup"""
    
    def __init__(self):
        self.setup_complete = self._check_setup_status()
        self.company_profile = self._load_company_profile()
    
    def _check_setup_status(self) -> bool:
        """Check if company profile has been configured"""
        try:
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
        """Load existing company profile"""
        try:
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
            
            return {}
        except Exception as e:
            logger.error(f"Error loading company profile: {e}")
            return {}
    
    def render_setup_wizard(self):
        """Render the company setup wizard"""
        if self.setup_complete:
            # Check if this is being called from admin UI for editing
            if st.session_state.get("show_company_wizard", False):
                # This is an edit operation from admin UI
                st.session_state.edit_company_profile = True
                self._render_setup_complete()
                return
            else:
                self._render_setup_complete()
                return
        
        # Check if this is an update or new setup
        is_update = bool(self.company_profile.get("company_name"))
        
        if is_update:
            # Only show description if not called from admin UI (to avoid duplication)
            if not st.session_state.get("show_company_wizard", False):
                st.markdown("""
                Update your company profile information. All fields are pre-filled with your current settings.
                
                Changes will be applied immediately and affect the entire application.
                """)
        else:
            st.markdown("# 🏢 Company Setup Wizard")
            st.markdown("---")
            st.markdown("""
            Welcome to Value Rollercoaster! Let's configure your company profile to get started.
            
            This setup will customize the app for your business.
            """)
        
        with st.form("company_setup_form"):
            st.markdown("### 📋 Company Information")
            
            # Basic Company Information
            col1, col2 = st.columns([2, 1])
            with col1:
                company_name = st.text_input(
                    "Company Name *",
                    value=self.company_profile.get("company_name", ""),
                    help="Your company's official name"
                )
            with col2:
                company_size = st.selectbox(
                    "Company Size",
                    ["Startup", "Small (1-50)", "Medium (51-200)", "Large (201-1000)", "Enterprise (1000+)"],
                    index=2
                )
            
            # Enhanced location options
            col1, col2 = st.columns(2)
            with col1:
                location_type = st.selectbox(
                    "Location Type *",
                    ["Single Location", "Multiple Locations", "Remote-First",
                     "Global Operations", "Regional Focus", "Local Market"],
                    index=0,
                    help="How your company is geographically organized"
                )
            with col2:
                location = st.text_input(
                    "Primary Location",
                    value=self.company_profile.get("location", ""),
                    help="Main office, headquarters, or primary base"
                )
            
            core_business = st.text_area(
                "Core Business Description *",
                value=self.company_profile.get("core_business", ""),
                help="Describe what your company does in 2-3 sentences",
                height=100
            )
            
            st.markdown("### 🎯 Target Market")
            
            # Initialize dynamic options in session state if not exists
            # Standard options (cannot be deleted)
            standard_customer_options = [
                "OEMs (Original Equipment Manufacturers)", "Distributors", "End Users", 
                "System Integrators", "Resellers", "Consultants", "Other"
            ]
            
            standard_industry_options = [
                "Mining", "Construction", "Agriculture", "Manufacturing", "Automotive",
                "Aerospace", "Marine", "Oil & Gas", "Utilities", "Other"
            ]
            
            # Get saved values from company profile (if editing existing profile)
            saved_customers = self.company_profile.get("target_customers", [])
            saved_industries = self.company_profile.get("industries_served", [])
            
            # Initialize or update dynamic options
            if "dynamic_customer_options" not in st.session_state:
                # Start with standard options
                st.session_state.dynamic_customer_options = standard_customer_options.copy()
            
            # Always ensure saved values are in the options list (even if session state exists)
            for customer in saved_customers:
                if customer not in st.session_state.dynamic_customer_options:
                    st.session_state.dynamic_customer_options.append(customer)
            
            if "dynamic_industry_options" not in st.session_state:
                # Start with standard options
                st.session_state.dynamic_industry_options = standard_industry_options.copy()
            
            # Always ensure saved values are in the options list (even if session state exists)
            for industry in saved_industries:
                if industry not in st.session_state.dynamic_industry_options:
                    st.session_state.dynamic_industry_options.append(industry)
            
            col1, col2 = st.columns(2)
            with col1:
                # Target Customers Multiselect
                # Get current selections from session state or profile
                default_customers = st.session_state.get("selected_customers", 
                    self.company_profile.get("target_customers", []))
                
                # Filter default values to only include those that exist in options (safety check)
                available_options = st.session_state.dynamic_customer_options
                valid_default_customers = [c for c in default_customers if c in available_options]
                
                target_customers = st.multiselect(
                    "Target Customers *",
                    available_options,
                    default=valid_default_customers,
                    help="Who are your primary customers?"
                )
                
                # Update session state with current selections
                st.session_state.selected_customers = target_customers
            
            # Custom Input Sections wrapped in expander
            with st.expander("➕ Add & Manage Custom Options", expanded=False):
                st.markdown("#### ➕ Add Custom Options")
                st.markdown("*Add custom customer types or industries that aren't in the standard list*")
                
                col_custom1, col_custom2 = st.columns(2)
                with col_custom1:
                    st.markdown("**➕ Add Custom Customer Type**")
                    custom_customer_input = st.text_input(
                        "Enter custom customer type",
                        key="custom_customer_input",
                        placeholder="e.g., Large Fleet Operators",
                        help="Type a custom customer type and use AI to validate or get suggestions"
                    )
                
                # AI Processing Buttons
                col_ai1, col_ai2 = st.columns(2)
                with col_ai1:
                    if st.button("🤖 AI Suggest", key="ai_suggest_customers"):
                        if custom_customer_input.strip():
                            st.session_state.ai_processing_customer = custom_customer_input
                        else:
                            # Get AI suggestions based on company profile
                            st.session_state.ai_suggesting_customers = True
                
                with col_ai2:
                    if st.button("✅ Validate & Add", key="validate_add_customer"):
                        if custom_customer_input.strip():
                            # Trigger AI validation first (don't add directly)
                            st.session_state.ai_processing_customer = custom_customer_input.strip()
                            st.rerun()
                
                # AI Processing Results
                if st.session_state.get("ai_processing_customer"):
                    with st.spinner("AI is processing..."):
                        import asyncio
                        result = asyncio.run(self._process_customer_with_ai(
                            st.session_state.ai_processing_customer,
                            self.company_profile
                        ))
                        st.session_state.ai_customer_result = result
                        st.session_state.ai_processing_customer = None
                        st.rerun()
                
                if st.session_state.get("ai_suggesting_customers"):
                    with st.spinner("AI is analyzing your company profile..."):
                        import asyncio
                        suggestions = asyncio.run(self._get_ai_customer_suggestions(self.company_profile))
                        st.session_state.ai_customer_suggestions = suggestions
                        st.session_state.ai_suggesting_customers = False
                        st.rerun()
                
                # Display AI Results
                if st.session_state.get("ai_customer_result"):
                    result = st.session_state.ai_customer_result
                    if result.get("suggested_match"):
                        st.info(f"💡 **Did you mean:** {result['suggested_match']}")
                        if st.button("✅ Use Suggested", key="use_suggested_customer"):
                            new_option = result['suggested_match']
                            if new_option not in st.session_state.dynamic_customer_options:
                                st.session_state.dynamic_customer_options.append(new_option)
                            # Add to selected customers via session state
                            current_selected = st.session_state.get("selected_customers", target_customers)
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_customers = current_selected
                            st.session_state.ai_customer_result = None
                            st.rerun()
                    elif result.get("is_valid"):
                        st.success("✅ Valid customer type")
                        if st.button("✅ Add to Selection", key="add_validated_customer"):
                            new_option = custom_customer_input.strip()
                            
                            # Check for duplicates
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_customer_options
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_customer_options:
                                    st.session_state.dynamic_customer_options.append(new_option)
                                # Add to selected customers via session state
                                current_selected = st.session_state.get("selected_customers", target_customers)
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_customers = current_selected
                                st.session_state.ai_customer_result = None
                                st.rerun()
                    else:
                        st.warning("⚠️ AI couldn't validate this entry. You can still add it manually.")
                        if st.button("⚠️ Add Anyway (Not Recommended)", key="add_unvalidated_customer"):
                            new_option = custom_customer_input.strip()
                            
                            # Check for duplicates even for unvalidated entries
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_customer_options
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_customer_options:
                                    st.session_state.dynamic_customer_options.append(new_option)
                                current_selected = st.session_state.get("selected_customers", target_customers)
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_customers = current_selected
                                st.session_state.ai_customer_result = None
                                st.rerun()
                
                # Display AI Suggestions
                if st.session_state.get("ai_customer_suggestions"):
                    st.markdown("**🤖 AI Suggestions:**")
                    for suggestion in st.session_state.ai_customer_suggestions[:5]:
                        suggestion_name = suggestion.get('name', suggestion) if isinstance(suggestion, dict) else suggestion
                        if st.button(f"➕ {suggestion_name}", key=f"add_suggested_customer_{suggestion_name}"):
                            new_option = suggestion_name
                            if new_option not in st.session_state.dynamic_customer_options:
                                st.session_state.dynamic_customer_options.append(new_option)
                            # Add to selected customers via session state
                            current_selected = st.session_state.get("selected_customers", target_customers)
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_customers = current_selected
                            st.session_state.ai_customer_suggestions = None
                            st.rerun()
                
                # Note: Direct add handlers removed - "Validate & Add" now triggers AI validation first
            
            with col2:
                # Industries Served Multiselect
                # Get current selections from session state or profile
                default_industries = st.session_state.get("selected_industries",
                    self.company_profile.get("industries_served", []))
                
                # Filter default values to only include those that exist in options (safety check)
                available_industry_options = st.session_state.dynamic_industry_options
                valid_default_industries = [i for i in default_industries if i in available_industry_options]
                
                industries_served = st.multiselect(
                    "Industries Served *",
                    available_industry_options,
                    default=valid_default_industries,
                    help="Which industries do you serve?"
                )
                
                # Update session state with current selections
                st.session_state.selected_industries = industries_served
                
                # Custom Input Section for Industries (below multiselect)
                st.markdown("---")
                st.markdown("**➕ Add Custom Industry**")
                
                custom_industry_input = st.text_input(
                    "Enter custom industry",
                    key="custom_industry_input",
                    placeholder="e.g., Port Logistics",
                    help="Type a custom industry and use AI to validate or get suggestions"
                )
                
                # AI Processing Buttons
                col_ai3, col_ai4 = st.columns(2)
                with col_ai3:
                    if st.button("🤖 AI Suggest", key="ai_suggest_industries"):
                        if custom_industry_input.strip():
                            st.session_state.ai_processing_industry = custom_industry_input
                        else:
                            # Get AI suggestions based on company profile
                            st.session_state.ai_suggesting_industries = True
                
                with col_ai4:
                    if st.button("✅ Validate & Add", key="validate_add_industry"):
                        if custom_industry_input.strip():
                            # Trigger AI validation first (don't add directly)
                            st.session_state.ai_processing_industry = custom_industry_input.strip()
                            st.rerun()
                
                # AI Processing Results
                if st.session_state.get("ai_processing_industry"):
                    with st.spinner("AI is processing..."):
                        import asyncio
                        result = asyncio.run(self._process_industry_with_ai(
                            st.session_state.ai_processing_industry,
                            self.company_profile
                        ))
                        st.session_state.ai_industry_result = result
                        st.session_state.ai_processing_industry = None
                        st.rerun()
                
                if st.session_state.get("ai_suggesting_industries"):
                    with st.spinner("AI is analyzing your company profile..."):
                        import asyncio
                        suggestions = asyncio.run(self._get_ai_industry_suggestions(self.company_profile))
                        st.session_state.ai_industry_suggestions = suggestions
                        st.session_state.ai_suggesting_industries = False
                        st.rerun()
                
                # Display AI Results
                if st.session_state.get("ai_industry_result"):
                    result = st.session_state.ai_industry_result
                    if result.get("suggested_match"):
                        st.info(f"💡 **Did you mean:** {result['suggested_match']}")
                        if st.button("✅ Use Suggested", key="use_suggested_industry"):
                            new_option = result['suggested_match']
                            if new_option not in st.session_state.dynamic_industry_options:
                                st.session_state.dynamic_industry_options.append(new_option)
                            # Add to selected industries via session state
                            current_selected = st.session_state.get("selected_industries", industries_served)
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_industries = current_selected
                            st.session_state.ai_industry_result = None
                            st.rerun()
                    elif result.get("is_valid"):
                        st.success("✅ Valid industry")
                        if st.button("✅ Add to Selection", key="add_validated_industry"):
                            new_option = custom_industry_input.strip()
                            
                            # Check for duplicates
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_industry_options
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_industry_options:
                                    st.session_state.dynamic_industry_options.append(new_option)
                                # Add to selected industries via session state
                                current_selected = st.session_state.get("selected_industries", industries_served)
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_industries = current_selected
                                st.session_state.ai_industry_result = None
                                st.rerun()
                    else:
                        st.warning("⚠️ AI couldn't validate this entry. You can still add it manually.")
                        if st.button("⚠️ Add Anyway (Not Recommended)", key="add_unvalidated_industry"):
                            new_option = custom_industry_input.strip()
                            
                            # Check for duplicates even for unvalidated entries
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_industry_options
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_industry_options:
                                    st.session_state.dynamic_industry_options.append(new_option)
                                current_selected = st.session_state.get("selected_industries", industries_served)
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_industries = current_selected
                                st.session_state.ai_industry_result = None
                                st.rerun()
                
                # Display AI Suggestions
                if st.session_state.get("ai_industry_suggestions"):
                    st.markdown("**🤖 AI Suggestions:**")
                    for suggestion in st.session_state.ai_industry_suggestions[:5]:
                        suggestion_name = suggestion.get('name', suggestion) if isinstance(suggestion, dict) else suggestion
                        if st.button(f"➕ {suggestion_name}", key=f"add_suggested_industry_{suggestion_name}"):
                            new_option = suggestion_name
                            if new_option not in st.session_state.dynamic_industry_options:
                                st.session_state.dynamic_industry_options.append(new_option)
                            # Add to selected industries via session state
                            current_selected = st.session_state.get("selected_industries", industries_served)
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_industries = current_selected
                            st.session_state.ai_industry_suggestions = None
                            st.rerun()
                
                # Note: Direct add handlers removed - "Validate & Add" now triggers AI validation first
                
                # Manage Custom Options Section (Delete custom values)
                st.markdown("---")
                st.markdown("#### 🗑️ Manage Custom Options")
                st.markdown("*Remove custom values you've added*")
                
                col_manage1, col_manage2 = st.columns(2)
                with col_manage1:
                    # Get custom customer options (not in standard list)
                    all_customer_options = st.session_state.dynamic_customer_options
                    custom_customers = [opt for opt in all_customer_options if opt not in standard_customer_options]
                    
                    if custom_customers:
                        st.markdown("**Custom Customer Types:**")
                        for custom_option in custom_customers:
                            col_del1, col_del2 = st.columns([3, 1])
                            with col_del1:
                                st.markdown(f"• {custom_option}")
                            with col_del2:
                                if st.button("🗑️ Delete", key=f"delete_customer_{custom_option}", use_container_width=True):
                                    # Remove from options list
                                    if custom_option in st.session_state.dynamic_customer_options:
                                        st.session_state.dynamic_customer_options.remove(custom_option)
                                    # Remove from selected if selected
                                    current_selected = st.session_state.get("selected_customers", [])
                                    if custom_option in current_selected:
                                        current_selected.remove(custom_option)
                                        st.session_state.selected_customers = current_selected
                                    st.rerun()
                    else:
                        st.info("No custom customer types added yet")
                
                with col_manage2:
                    # Get custom industry options (not in standard list)
                    all_industry_options = st.session_state.dynamic_industry_options
                    custom_industries = [opt for opt in all_industry_options if opt not in standard_industry_options]
                    
                    if custom_industries:
                        st.markdown("**Custom Industries:**")
                        for custom_option in custom_industries:
                            col_del3, col_del4 = st.columns([3, 1])
                            with col_del3:
                                st.markdown(f"• {custom_option}")
                            with col_del4:
                                if st.button("🗑️ Delete", key=f"delete_industry_{custom_option}", use_container_width=True):
                                    # Remove from options list
                                    if custom_option in st.session_state.dynamic_industry_options:
                                        st.session_state.dynamic_industry_options.remove(custom_option)
                                    # Remove from selected if selected
                                    current_selected = st.session_state.get("selected_industries", [])
                                    if custom_option in current_selected:
                                        current_selected.remove(custom_option)
                                        st.session_state.selected_industries = current_selected
                                    st.rerun()
                    else:
                        st.info("No custom industries added yet")
            
            st.markdown("### 🛠️ Products & Services")
            
            products = st.text_area(
                "Products and Services *",
                value=self.company_profile.get("products", ""),
                help="Describe your main products and services",
                height=100
            )
            
            value_propositions = st.text_area(
                "Key Value Propositions",
                value=self.company_profile.get("value_propositions", ""),
                help="What makes your products/services unique? What value do you provide?",
                height=100
            )
            
            st.markdown("### 🧠 Business Intelligence")
            st.markdown("*Help AI models understand your company's business model and market position*")
            
            # Company Classification
            col1, col2 = st.columns(2)
            with col1:
                company_type = st.selectbox(
                    "Company Type *",
                    ["Manufacturer & Technology Owner", "Service Provider", "Technology Company", 
                     "Consulting", "Platform Provider", "Distributor", "Other"],
                    index=0,
                    help="Primary business classification"
                )
            with col2:
                business_model = st.selectbox(
                    "Business Model *",
                    ["B2B OEM Supplier", "B2B", "B2C", "SaaS", "Consulting", "Platform", 
                     "Marketplace", "Subscription", "Other"],
                    index=0,
                    help="How you generate revenue"
                )
            
            # Value Delivery & Market Position
            col1, col2 = st.columns(2)
            with col1:
                value_delivery_method = st.selectbox(
                    "Value Delivery Method *",
                    ["Product", "Service", "Platform", "Solution", "Consultation", "Other"],
                    index=0,
                    help="How you deliver value to customers"
                )
            with col2:
                market_position = st.selectbox(
                    "Market Position *",
                    ["Leader", "Challenger", "Specialist", "Niche", "Emerging", "Other"],
                    index=0,
                    help="Your position in the market"
                )
            
            # Company Characteristics
            col1, col2 = st.columns(2)
            with col1:
                company_size_bi = st.selectbox(
                    "Company Size (BI) *",
                    ["Small", "Medium", "Large", "Enterprise"],
                    index=1,
                    help="Company size for business intelligence"
                )
            with col2:
                maturity_stage = st.selectbox(
                    "Maturity Stage *",
                    ["Startup", "Growing", "Established", "Mature"],
                    index=3,
                    help="Current stage of company development"
                )
            
            # Geographic & Industry Focus
            col1, col2 = st.columns(2)
            with col1:
                geographic_scope = st.selectbox(
                    "Geographic Scope *",
                    ["Local", "Regional", "National", "Global"],
                    index=3,
                    help="Geographic reach of your business"
                )
            with col2:
                industry_focus = st.selectbox(
                    "Industry Focus *",
                    ["Industrial Equipment", "Manufacturing", "Technology", "Services", 
                     "Healthcare", "Finance", "Retail", "Other"],
                    index=0,
                    help="Primary industry focus"
                )
            
            # Revenue & Customer Relationships
            col1, col2 = st.columns(2)
            with col1:
                revenue_model = st.selectbox(
                    "Revenue Model *",
                    ["Product Sales", "Subscription", "Consulting", "Licensing", 
                     "Commission", "Advertising", "Other"],
                    index=0,
                    help="How you generate revenue"
                )
            with col2:
                customer_relationship_type = st.selectbox(
                    "Customer Relationship Type *",
                    ["Transactional", "Partnership", "Subscription", "Long-term Partnership", 
                     "One-time", "Other"],
                    index=3,
                    help="Nature of customer relationships"
                )
            
            # Innovation & Competitive Advantage
            col1, col2 = st.columns(2)
            with col1:
                innovation_focus = st.selectbox(
                    "Innovation Focus *",
                    ["Product & Technology Innovation", "Process Innovation", 
                     "Business Model Innovation", "Service Innovation", "Other"],
                    index=0,
                    help="Primary focus of innovation efforts"
                )
            with col2:
                competitive_advantage_type = st.selectbox(
                    "Competitive Advantage Type *",
                    ["Technology Owner Expertise", "Scale", "Technology", "Service", 
                     "Cost Leadership", "Brand", "Other"],
                    index=0,
                    help="Your main competitive advantage"
                )
            
            st.markdown("### 🎨 Optional: Branding")
            
            col1, col2 = st.columns(2)
            with col1:
                primary_color = st.color_picker(
                    "Primary Brand Color",
                    value=self.company_profile.get("primary_color", "#1f77b4"),
                    help="Color for charts and UI elements"
                )
            with col2:
                logo_url = st.text_input(
                    "Logo URL (optional)",
                    value=self.company_profile.get("logo_url", ""),
                    help="URL to your company logo"
                )
            
            # Submit button
            button_text = "🔄 Update Profile" if is_update else "🚀 Complete Setup"
            submitted = st.form_submit_button(button_text, type="primary", use_container_width=True)
            
            if submitted:
                if self._validate_form(company_name, core_business, target_customers, industries_served, products):
                    self._save_company_profile({
                        "company_name": company_name,
                        "company_size": company_size,
                        "location": location,
                        "location_type": location_type,
                        "core_business": core_business,
                        "target_customers": target_customers,
                        "industries_served": industries_served,
                        "products": products,
                        "value_propositions": value_propositions,
                        "primary_color": primary_color,
                        "logo_url": logo_url,
                        "business_intelligence": {
                            "company_type": company_type,
                            "business_model": business_model,
                            "value_delivery_method": value_delivery_method,
                            "market_position": market_position,
                            "company_size": company_size_bi,
                            "maturity_stage": maturity_stage,
                            "geographic_scope": geographic_scope,
                            "industry_focus": industry_focus,
                            "revenue_model": revenue_model,
                            "customer_relationship_type": customer_relationship_type,
                            "innovation_focus": innovation_focus,
                            "competitive_advantage_type": competitive_advantage_type
                        },
                        "setup_complete": True,
                        "setup_date": datetime.now().isoformat(),
                        "company_id": str(uuid.uuid4())
                    })
                    if is_update:
                        st.success("✅ Company profile updated successfully!")
                        st.info("🔄 Changes have been applied to the application.")
                    else:
                        st.success("✅ Company profile saved successfully!")
                        st.info("🔄 Please refresh the page to start using the app with your company profile.")
                    st.rerun()
    
    def _validate_form(self, company_name: Optional[str], core_business: Optional[str], 
                      target_customers: list, industries_served: list, products: Optional[str]) -> bool:
        """Validate the setup form"""
        return all([
            company_name and company_name.strip(),
            core_business and core_business.strip(),
            len(target_customers) > 0,
            len(industries_served) > 0,
            products and products.strip()
        ])
    
    def _save_company_profile(self, profile_data: Dict[str, Any]) -> bool:
        """Save company profile to database"""
        try:
            from app.database import QDRANT_CLIENT
            from qdrant_client.models import PointStruct
            
            # Create point for company profile
            point_id = hash(profile_data["company_id"]) % (2**63)
            vector = [0.0] * 128  # Dummy vector for company profile
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=profile_data
            )
            
            # Upsert to database
            result = QDRANT_CLIENT.upsert(
                collection_name="company_profiles",
                points=[point]
            )
            
            logger.info(f"Company profile saved for: {profile_data['company_name']}")
            logger.info(f"Database upsert result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving company profile: {e}")
            st.error(f"❌ Error saving company profile: {e}")
            return False
    
    def _render_setup_complete(self):
        """Render setup complete message"""
        # Check if user wants to edit the profile
        if st.session_state.get("edit_company_profile", False):
            # Title is already rendered by the UI, so we don't need to render it again
            # Just show the edit form
            self._render_edit_form()
            return
        
        st.markdown("# ✅ Company Setup Complete")
        st.markdown("---")
        
        st.success("🎉 Your company profile has been configured successfully!")
        
        # Display current company profile
        st.markdown("### 📋 Current Company Profile")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Company:** {self.company_profile.get('company_name', 'N/A')}")
            st.markdown(f"**Size:** {self.company_profile.get('company_size', 'N/A')}")
            st.markdown(f"**Location:** {self.company_profile.get('location', 'N/A')}")
            st.markdown(f"**Location Type:** {self.company_profile.get('location_type', 'N/A')}")
        
        with col2:
            # Convert setup date to human-readable format
            setup_date = self.company_profile.get('setup_date', 'N/A')
            if setup_date != 'N/A':
                try:
                    from datetime import datetime
                    # Parse the ISO format date
                    dt = datetime.fromisoformat(setup_date.replace('Z', '+00:00'))
                    # Format as human-readable
                    human_date = dt.strftime("%B %d, %Y at %I:%M %p")
                    st.markdown(f"**Setup Date:** {human_date}")
                except:
                    st.markdown(f"**Setup Date:** {setup_date}")
            else:
                st.markdown(f"**Setup Date:** {setup_date}")
        
        st.markdown("### 🎯 Target Market")
        st.markdown(f"**Target Customers:** {', '.join(self.company_profile.get('target_customers', []))}")
        st.markdown(f"**Industries Served:** {', '.join(self.company_profile.get('industries_served', []))}")
        
        st.markdown("### 🛠️ Business Description")
        st.markdown(f"**Core Business:** {self.company_profile.get('core_business', 'N/A')}")
        st.markdown(f"**Products/Services:** {self.company_profile.get('products', 'N/A')}")
        
        # Display Business Intelligence
        bi_data = self.company_profile.get("business_intelligence", {})
        if bi_data:
            st.markdown("### 🧠 Business Intelligence")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Company Type:** {bi_data.get('company_type', 'N/A')}")
                st.markdown(f"**Business Model:** {bi_data.get('business_model', 'N/A')}")
                st.markdown(f"**Market Position:** {bi_data.get('market_position', 'N/A')}")
                st.markdown(f"**Maturity Stage:** {bi_data.get('maturity_stage', 'N/A')}")
                st.markdown(f"**Geographic Scope:** {bi_data.get('geographic_scope', 'N/A')}")
            
            with col2:
                st.markdown(f"**Value Delivery:** {bi_data.get('value_delivery_method', 'N/A')}")
                st.markdown(f"**Company Size (BI):** {bi_data.get('company_size', 'N/A')}")
                st.markdown(f"**Industry Focus:** {bi_data.get('industry_focus', 'N/A')}")
                st.markdown(f"**Revenue Model:** {bi_data.get('revenue_model', 'N/A')}")
                st.markdown(f"**Customer Relations:** {bi_data.get('customer_relationship_type', 'N/A')}")
            
            st.markdown(f"**Innovation Focus:** {bi_data.get('innovation_focus', 'N/A')}")
            st.markdown(f"**Competitive Advantage:** {bi_data.get('competitive_advantage_type', 'N/A')}")
        
        # Option to edit profile
        if st.button("✏️ Edit Company Profile", type="secondary"):
            st.session_state.edit_company_profile = True
            st.rerun()
    
    def get_company_profile(self) -> Dict[str, Any]:
        """Get the current company profile"""
        return self.company_profile
    
    def is_setup_complete(self) -> bool:
        """Check if setup is complete"""
        return self.setup_complete
    
    def _render_edit_form(self):
        """Render the edit form for updating company profile"""
        # Refresh the company profile to get the latest data
        self.company_profile = self._load_company_profile()
        
        with st.form("edit_company_form"):
            st.markdown("### 📋 Company Information")
            
            # Basic Company Information
            col1, col2 = st.columns([2, 1])
            with col1:
                company_name = st.text_input(
                    "Company Name *",
                    value=self.company_profile.get("company_name", ""),
                    help="Your company's official name"
                )
            with col2:
                company_size = st.selectbox(
                    "Company Size *",
                    options=["Small (1-50)", "Medium (51-200)", "Large (201-1000)", "Enterprise (1000+)"],
                    index=["Small (1-50)", "Medium (51-200)", "Large (201-1000)", "Enterprise (1000+)"].index(
                        self.company_profile.get("company_size", "Medium (51-200)")
                    ),
                    help="Number of employees"
                )
            
            # Enhanced location options
            col1, col2 = st.columns(2)
            with col1:
                location_type = st.selectbox(
                    "Location Type *",
                    options=["Single Location", "Multiple Locations", "Remote-First",
                            "Global Operations", "Regional Focus", "Local Market"],
                    index=["Single Location", "Multiple Locations", "Remote-First",
                           "Global Operations", "Regional Focus", "Local Market"].index(
                        self.company_profile.get("location_type", "Single Location")
                    ),
                    help="How your company is geographically organized"
                )
            with col2:
                location = st.text_input(
                    "Primary Location *",
                    value=self.company_profile.get("location", ""),
                    help="Main office, headquarters, or primary base"
                )
            
            core_business = st.text_area(
                "Core Business Description *",
                value=self.company_profile.get("core_business", ""),
                help="What does your company do?",
                height=100
            )
            
            # Store form values in session state before closing
            if st.form_submit_button("💾 Save Company Info", use_container_width=False, type="secondary"):
                st.session_state.company_name_edit = company_name
                st.session_state.company_size_edit = company_size
                st.session_state.location_edit = location
                st.session_state.location_type_edit = location_type
                st.session_state.core_business_edit = core_business
        
        # Target Market Section OUTSIDE the form (so multiselects and custom inputs work properly)
        st.markdown("### 🎯 Target Market")
        
        # Initialize dynamic options in session state if not exists
        # Standard options (cannot be deleted)
        standard_customer_options = [
            "OEMs (Original Equipment Manufacturers)", "Distributors", "End Users", 
            "System Integrators", "Resellers", "Consultants", "Other"
        ]
        
        standard_industry_options = [
            "Mining", "Construction", "Agriculture", "Manufacturing", "Automotive",
            "Aerospace", "Marine", "Oil & Gas", "Utilities", "Other"
        ]
        
        # Get saved values from company profile
        saved_customers = self.company_profile.get("target_customers", [])
        saved_industries = self.company_profile.get("industries_served", [])
        
        # Initialize or update dynamic options
        if "dynamic_customer_options_edit" not in st.session_state:
            # Start with standard options
            st.session_state.dynamic_customer_options_edit = standard_customer_options.copy()
        
        # Always ensure saved values are in the options list (even if session state exists)
        for customer in saved_customers:
            if customer not in st.session_state.dynamic_customer_options_edit:
                st.session_state.dynamic_customer_options_edit.append(customer)
        
        if "dynamic_industry_options_edit" not in st.session_state:
            # Start with standard options
            st.session_state.dynamic_industry_options_edit = standard_industry_options.copy()
        
        # Always ensure saved values are in the options list (even if session state exists)
        for industry in saved_industries:
            if industry not in st.session_state.dynamic_industry_options_edit:
                st.session_state.dynamic_industry_options_edit.append(industry)
        
        # Track custom options (for deletion)
        if "custom_customer_options_edit" not in st.session_state:
            st.session_state.custom_customer_options_edit = []
        
        if "custom_industry_options_edit" not in st.session_state:
            st.session_state.custom_industry_options_edit = []
        
        col1, col2 = st.columns(2)
        with col1:
            # Target Customers Multiselect
            # Get current selections from session state or profile
            default_customers = st.session_state.get("selected_customers_edit", 
                self.company_profile.get("target_customers", []))
            
            # Filter default values to only include those that exist in options (safety check)
            available_options = st.session_state.dynamic_customer_options_edit
            valid_default_customers = [c for c in default_customers if c in available_options]
            
            target_customers = st.multiselect(
                "Target Customers *",
                available_options,
                default=valid_default_customers,
                help="Who are your primary customers?"
            )
            
            # Update session state with current selections
            st.session_state.selected_customers_edit = target_customers
        
        with col2:
            # Industries Served Multiselect
            # Get current selections from session state or profile
            default_industries = st.session_state.get("selected_industries_edit",
                self.company_profile.get("industries_served", []))
            
            # Filter default values to only include those that exist in options (safety check)
            available_industry_options = st.session_state.dynamic_industry_options_edit
            valid_default_industries = [i for i in default_industries if i in available_industry_options]
            
            industries_served = st.multiselect(
                "Industries Served *",
                available_industry_options,
                default=valid_default_industries,
                help="Which industries do you serve?"
            )
            
            # Update session state with current selections
            st.session_state.selected_industries_edit = industries_served
        
        # Custom Input Sections (buttons work here since we're outside any form)
        with st.expander("➕ Add & Manage Custom Options", expanded=False):
            st.markdown("#### ➕ Add Custom Options")
            st.markdown("*Add custom customer types or industries that aren't in the standard list*")
            
            col_custom1, col_custom2 = st.columns(2)
            with col_custom1:
                st.markdown("**➕ Add Custom Customer Type**")
                custom_customer_input = st.text_input(
                    "Enter custom customer type",
                    key="custom_customer_input_edit",
                    placeholder="e.g., Large Fleet Operators",
                    help="Type a custom customer type and use AI to validate or get suggestions"
                )
                
                # AI Processing Buttons
                col_ai1, col_ai2 = st.columns(2)
                with col_ai1:
                    if st.button("🤖 AI Suggest", key="ai_suggest_customers_edit"):
                        if custom_customer_input.strip():
                            st.session_state.ai_processing_customer_edit = custom_customer_input
                        else:
                            st.session_state.ai_suggesting_customers_edit = True
                        st.rerun()
                
                with col_ai2:
                    if st.button("✅ Validate & Add", key="validate_add_customer_edit"):
                        if custom_customer_input.strip():
                            # Trigger AI validation first (don't add directly)
                            st.session_state.ai_processing_customer_edit = custom_customer_input.strip()
                            st.rerun()
                
                # AI Processing Results
                if st.session_state.get("ai_processing_customer_edit"):
                    with st.spinner("AI is processing..."):
                        import asyncio
                        result = asyncio.run(self._process_customer_with_ai(
                            st.session_state.ai_processing_customer_edit,
                            self.company_profile
                        ))
                        st.session_state.ai_customer_result_edit = result
                        st.session_state.ai_processing_customer_edit = None
                        st.rerun()
                
                if st.session_state.get("ai_suggesting_customers_edit"):
                    with st.spinner("AI is analyzing your company profile..."):
                        import asyncio
                        suggestions = asyncio.run(self._get_ai_customer_suggestions(self.company_profile))
                        st.session_state.ai_customer_suggestions_edit = suggestions
                        st.session_state.ai_suggesting_customers_edit = False
                        st.rerun()
                
                # Display AI Results
                if st.session_state.get("ai_customer_result_edit"):
                    result = st.session_state.ai_customer_result_edit
                    if result.get("suggested_match"):
                        st.info(f"💡 **Did you mean:** {result['suggested_match']}")
                        if st.button("✅ Use Suggested", key="use_suggested_customer_edit"):
                            new_option = result['suggested_match']
                            if new_option not in st.session_state.dynamic_customer_options_edit:
                                st.session_state.dynamic_customer_options_edit.append(new_option)
                            current_selected = st.session_state.get("selected_customers_edit", [])
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_customers_edit = current_selected
                            st.session_state.ai_customer_result_edit = None
                            st.rerun()
                    elif result.get("is_valid"):
                        st.success("✅ Valid customer type")
                        if st.button("✅ Add to Selection", key="add_validated_customer_edit"):
                            new_option = custom_customer_input.strip()
                            
                            # Check for duplicates
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_customer_options_edit
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_customer_options_edit:
                                    st.session_state.dynamic_customer_options_edit.append(new_option)
                                current_selected = st.session_state.get("selected_customers_edit", [])
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_customers_edit = current_selected
                                st.session_state.ai_customer_result_edit = None
                                st.rerun()
                    else:
                        st.warning("⚠️ AI couldn't validate this entry. You can still add it manually.")
                        if st.button("⚠️ Add Anyway (Not Recommended)", key="add_unvalidated_customer_edit"):
                            new_option = custom_customer_input.strip()
                            
                            # Check for duplicates even for unvalidated entries
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_customer_options_edit
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_customer_options_edit:
                                    st.session_state.dynamic_customer_options_edit.append(new_option)
                                current_selected = st.session_state.get("selected_customers_edit", [])
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_customers_edit = current_selected
                                st.session_state.ai_customer_result_edit = None
                                st.rerun()
                
                # Display AI Suggestions
                if st.session_state.get("ai_customer_suggestions_edit"):
                    st.markdown("**🤖 AI Suggestions:**")
                    for suggestion in st.session_state.ai_customer_suggestions_edit[:5]:
                        suggestion_name = suggestion.get('name', suggestion) if isinstance(suggestion, dict) else suggestion
                        if st.button(f"➕ {suggestion_name}", key=f"add_suggested_customer_edit_{suggestion_name}"):
                            new_option = suggestion_name
                            if new_option not in st.session_state.dynamic_customer_options_edit:
                                st.session_state.dynamic_customer_options_edit.append(new_option)
                            current_selected = st.session_state.get("selected_customers_edit", [])
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_customers_edit = current_selected
                            st.session_state.ai_customer_suggestions_edit = None
                            st.rerun()
                
                # Note: Direct add handlers removed - "Validate & Add" now triggers AI validation first
            
            with col_custom2:
                st.markdown("**➕ Add Custom Industry**")
                custom_industry_input = st.text_input(
                    "Enter custom industry",
                    key="custom_industry_input_edit",
                    placeholder="e.g., Port Logistics",
                    help="Type a custom industry and use AI to validate or get suggestions"
                )
                
                # AI Processing Buttons
                col_ai3, col_ai4 = st.columns(2)
                with col_ai3:
                    if st.button("🤖 AI Suggest", key="ai_suggest_industries_edit"):
                        if custom_industry_input.strip():
                            st.session_state.ai_processing_industry_edit = custom_industry_input
                        else:
                            st.session_state.ai_suggesting_industries_edit = True
                        st.rerun()
                
                with col_ai4:
                    if st.button("✅ Validate & Add", key="validate_add_industry_edit"):
                        if custom_industry_input.strip():
                            # Trigger AI validation first (don't add directly)
                            st.session_state.ai_processing_industry_edit = custom_industry_input.strip()
                            st.rerun()
                
                # AI Processing Results
                if st.session_state.get("ai_processing_industry_edit"):
                    with st.spinner("AI is processing..."):
                        import asyncio
                        result = asyncio.run(self._process_industry_with_ai(
                            st.session_state.ai_processing_industry_edit,
                            self.company_profile
                        ))
                        st.session_state.ai_industry_result_edit = result
                        st.session_state.ai_processing_industry_edit = None
                        st.rerun()
                
                if st.session_state.get("ai_suggesting_industries_edit"):
                    with st.spinner("AI is analyzing your company profile..."):
                        import asyncio
                        suggestions = asyncio.run(self._get_ai_industry_suggestions(self.company_profile))
                        st.session_state.ai_industry_suggestions_edit = suggestions
                        st.session_state.ai_suggesting_industries_edit = False
                        st.rerun()
                
                # Display AI Results
                if st.session_state.get("ai_industry_result_edit"):
                    result = st.session_state.ai_industry_result_edit
                    if result.get("suggested_match"):
                        st.info(f"💡 **Did you mean:** {result['suggested_match']}")
                        if st.button("✅ Use Suggested", key="use_suggested_industry_edit"):
                            new_option = result['suggested_match']
                            if new_option not in st.session_state.dynamic_industry_options_edit:
                                st.session_state.dynamic_industry_options_edit.append(new_option)
                            current_selected = st.session_state.get("selected_industries_edit", [])
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_industries_edit = current_selected
                            st.session_state.ai_industry_result_edit = None
                            st.rerun()
                    elif result.get("is_valid"):
                        st.success("✅ Valid industry")
                        if st.button("✅ Add to Selection", key="add_validated_industry_edit"):
                            new_option = custom_industry_input.strip()
                            
                            # Check for duplicates
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_industry_options_edit
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_industry_options_edit:
                                    st.session_state.dynamic_industry_options_edit.append(new_option)
                                current_selected = st.session_state.get("selected_industries_edit", [])
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_industries_edit = current_selected
                                st.session_state.ai_industry_result_edit = None
                                st.rerun()
                    else:
                        st.warning("⚠️ AI couldn't validate this entry. You can still add it manually.")
                        if st.button("⚠️ Add Anyway (Not Recommended)", key="add_unvalidated_industry_edit"):
                            new_option = custom_industry_input.strip()
                            
                            # Check for duplicates even for unvalidated entries
                            is_duplicate, similar_option = self._check_duplicate(
                                new_option, 
                                st.session_state.dynamic_industry_options_edit
                            )
                            
                            if is_duplicate:
                                st.error(f"❌ **Duplicate detected!** '{new_option}' is very similar to existing option: '{similar_option}'. Please use the existing option or choose a different name.")
                            else:
                                if new_option not in st.session_state.dynamic_industry_options_edit:
                                    st.session_state.dynamic_industry_options_edit.append(new_option)
                                current_selected = st.session_state.get("selected_industries_edit", [])
                                if new_option not in current_selected:
                                    current_selected.append(new_option)
                                st.session_state.selected_industries_edit = current_selected
                                st.session_state.ai_industry_result_edit = None
                                st.rerun()
                
                # Display AI Suggestions
                if st.session_state.get("ai_industry_suggestions_edit"):
                    st.markdown("**🤖 AI Suggestions:**")
                    for suggestion in st.session_state.ai_industry_suggestions_edit[:5]:
                        suggestion_name = suggestion.get('name', suggestion) if isinstance(suggestion, dict) else suggestion
                        if st.button(f"➕ {suggestion_name}", key=f"add_suggested_industry_edit_{suggestion_name}"):
                            new_option = suggestion_name
                            if new_option not in st.session_state.dynamic_industry_options_edit:
                                st.session_state.dynamic_industry_options_edit.append(new_option)
                            current_selected = st.session_state.get("selected_industries_edit", [])
                            if new_option not in current_selected:
                                current_selected.append(new_option)
                            st.session_state.selected_industries_edit = current_selected
                            st.session_state.ai_industry_suggestions_edit = None
                            st.rerun()
                
                # Note: Direct add handlers removed - "Validate & Add" now triggers AI validation first
            
            # Manage Custom Options Section (Delete custom values)
            st.markdown("---")
            st.markdown("#### 🗑️ Manage Custom Options")
            st.markdown("*Remove custom values you've added*")
            
            col_manage1, col_manage2 = st.columns(2)
            with col_manage1:
                # Get custom customer options (not in standard list)
                all_customer_options = st.session_state.dynamic_customer_options_edit
                custom_customers = [opt for opt in all_customer_options if opt not in standard_customer_options]
                
                if custom_customers:
                    st.markdown("**Custom Customer Types:**")
                    for custom_option in custom_customers:
                        col_del1, col_del2 = st.columns([3, 1])
                        with col_del1:
                            st.markdown(f"• {custom_option}")
                        with col_del2:
                            if st.button("🗑️ Delete", key=f"delete_customer_{custom_option}", use_container_width=True):
                                # Remove from options list
                                if custom_option in st.session_state.dynamic_customer_options_edit:
                                    st.session_state.dynamic_customer_options_edit.remove(custom_option)
                                # Remove from selected if selected
                                current_selected = st.session_state.get("selected_customers_edit", [])
                                if custom_option in current_selected:
                                    current_selected.remove(custom_option)
                                    st.session_state.selected_customers_edit = current_selected
                                st.rerun()
                else:
                    st.info("No custom customer types added yet")
            
            with col_manage2:
                # Get custom industry options (not in standard list)
                all_industry_options = st.session_state.dynamic_industry_options_edit
                custom_industries = [opt for opt in all_industry_options if opt not in standard_industry_options]
                
                if custom_industries:
                    st.markdown("**Custom Industries:**")
                    for custom_option in custom_industries:
                        col_del3, col_del4 = st.columns([3, 1])
                        with col_del3:
                            st.markdown(f"• {custom_option}")
                        with col_del4:
                            if st.button("🗑️ Delete", key=f"delete_industry_{custom_option}", use_container_width=True):
                                # Remove from options list
                                if custom_option in st.session_state.dynamic_industry_options_edit:
                                    st.session_state.dynamic_industry_options_edit.remove(custom_option)
                                # Remove from selected if selected
                                current_selected = st.session_state.get("selected_industries_edit", [])
                                if custom_option in current_selected:
                                    current_selected.remove(custom_option)
                                    st.session_state.selected_industries_edit = current_selected
                                st.rerun()
                else:
                    st.info("No custom industries added yet")
            
        # Re-open form for Products & Services and Business Intelligence sections
        with st.form("edit_company_form_part2"):
            st.markdown("### 🛠️ Products & Services")
            
            products = st.text_area(
                "Products & Services *",
                value=self.company_profile.get("products", ""),
                help="Describe your main products and services",
                height=100
            )
            
            value_propositions = st.text_area(
                "Key Value Propositions",
                value=self.company_profile.get("value_propositions", ""),
                help="What makes your company unique?",
                height=100
            )
            
            st.markdown("### 🧠 Business Intelligence")
            st.markdown("*Help AI models understand your company's business model and market position*")
            
            # Get existing business intelligence data
            bi_data = self.company_profile.get("business_intelligence", {})
            
            # Company Classification
            col1, col2 = st.columns(2)
            with col1:
                company_type = st.selectbox(
                    "Company Type *",
                    options=["Manufacturer & Technology Owner", "Service Provider", "Technology Company", 
                            "Consulting", "Platform Provider", "Distributor", "Other"],
                    index=["Manufacturer & Technology Owner", "Service Provider", "Technology Company", 
                           "Consulting", "Platform Provider", "Distributor", "Other"].index(
                        bi_data.get("company_type", "Manufacturer & Technology Owner")
                    ),
                    help="Primary business classification"
                )
            with col2:
                business_model = st.selectbox(
                    "Business Model *",
                    options=["B2B OEM Supplier", "B2B", "B2C", "SaaS", "Consulting", "Platform", 
                            "Marketplace", "Subscription", "Other"],
                    index=["B2B OEM Supplier", "B2B", "B2C", "SaaS", "Consulting", "Platform", 
                           "Marketplace", "Subscription", "Other"].index(
                        bi_data.get("business_model", "B2B OEM Supplier")
                    ),
                    help="How you generate revenue"
                )
            
            # Value Delivery & Market Position
            col1, col2 = st.columns(2)
            with col1:
                value_delivery_method = st.selectbox(
                    "Value Delivery Method *",
                    options=["Product", "Service", "Platform", "Solution", "Consultation", "Other"],
                    index=["Product", "Service", "Platform", "Solution", "Consultation", "Other"].index(
                        bi_data.get("value_delivery_method", "Product")
                    ),
                    help="How you deliver value to customers"
                )
            with col2:
                market_position = st.selectbox(
                    "Market Position *",
                    options=["Leader", "Challenger", "Specialist", "Niche", "Emerging", "Other"],
                    index=["Leader", "Challenger", "Specialist", "Niche", "Emerging", "Other"].index(
                        bi_data.get("market_position", "Leader")
                    ),
                    help="Your position in the market"
                )
            
            # Company Characteristics
            col1, col2 = st.columns(2)
            with col1:
                company_size_bi = st.selectbox(
                    "Company Size (BI) *",
                    options=["Small", "Medium", "Large", "Enterprise"],
                    index=["Small", "Medium", "Large", "Enterprise"].index(
                        bi_data.get("company_size", "Medium")
                    ),
                    help="Company size for business intelligence"
                )
            with col2:
                maturity_stage = st.selectbox(
                    "Maturity Stage *",
                    options=["Startup", "Growing", "Established", "Mature"],
                    index=["Startup", "Growing", "Established", "Mature"].index(
                        bi_data.get("maturity_stage", "Mature")
                    ),
                    help="Current stage of company development"
                )
            
            # Geographic & Industry Focus
            col1, col2 = st.columns(2)
            with col1:
                geographic_scope = st.selectbox(
                    "Geographic Scope *",
                    options=["Local", "Regional", "National", "Global"],
                    index=["Local", "Regional", "National", "Global"].index(
                        bi_data.get("geographic_scope", "Global")
                    ),
                    help="Geographic reach of your business"
                )
            with col2:
                industry_focus = st.selectbox(
                    "Industry Focus *",
                    options=["Industrial Equipment", "Manufacturing", "Technology", "Services", 
                            "Healthcare", "Finance", "Retail", "Other"],
                    index=["Industrial Equipment", "Manufacturing", "Technology", "Services", 
                           "Healthcare", "Finance", "Retail", "Other"].index(
                        bi_data.get("industry_focus", "Industrial Equipment")
                    ),
                    help="Primary industry focus"
                )
            
            # Revenue & Customer Relationships
            col1, col2 = st.columns(2)
            with col1:
                revenue_model = st.selectbox(
                    "Revenue Model *",
                    options=["Product Sales", "Subscription", "Consulting", "Licensing", 
                            "Commission", "Advertising", "Other"],
                    index=["Product Sales", "Subscription", "Consulting", "Licensing", 
                           "Commission", "Advertising", "Other"].index(
                        bi_data.get("revenue_model", "Product Sales")
                    ),
                    help="How you generate revenue"
                )
            with col2:
                customer_relationship_type = st.selectbox(
                    "Customer Relationship Type *",
                    options=["Transactional", "Partnership", "Subscription", "Long-term Partnership", 
                            "One-time", "Other"],
                    index=["Transactional", "Partnership", "Subscription", "Long-term Partnership", 
                           "One-time", "Other"].index(
                        bi_data.get("customer_relationship_type", "Long-term Partnership")
                    ),
                    help="Nature of customer relationships"
                )
            
            # Innovation & Competitive Advantage
            col1, col2 = st.columns(2)
            with col1:
                innovation_focus = st.selectbox(
                    "Innovation Focus *",
                    options=["Product & Technology Innovation", "Process Innovation", 
                            "Business Model Innovation", "Service Innovation", "Other"],
                    index=["Product & Technology Innovation", "Process Innovation", 
                           "Business Model Innovation", "Service Innovation", "Other"].index(
                        bi_data.get("innovation_focus", "Product & Technology Innovation")
                    ),
                    help="Primary focus of innovation efforts"
                )
            with col2:
                competitive_advantage_type = st.selectbox(
                    "Competitive Advantage Type *",
                    options=["Technology Owner Expertise", "Scale", "Technology", "Service", 
                            "Cost Leadership", "Brand", "Other"],
                    index=["Technology Owner Expertise", "Scale", "Technology", "Service", 
                           "Cost Leadership", "Brand", "Other"].index(
                        bi_data.get("competitive_advantage_type", "Technology Owner Expertise")
                    ),
                    help="Your main competitive advantage"
                )
            
            st.markdown("### 🎨 Branding (Optional)")
            
            col1, col2 = st.columns(2)
            with col1:
                primary_color = st.color_picker(
                    "Primary Brand Color",
                    value=self.company_profile.get("primary_color", "#1f77b4"),
                    help="Your company's main brand color"
                )
            
            with col2:
                logo_url = st.text_input(
                    "Logo URL (optional)",
                    value=self.company_profile.get("logo_url", ""),
                    help="URL to your company logo"
                )
            
            # Form buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.form_submit_button("🔄 Update Profile", type="primary", use_container_width=True):
                    # Get all values from session state (may have been updated)
                    final_company_name = st.session_state.get("company_name_edit", 
                        self.company_profile.get("company_name", ""))
                    final_company_size = st.session_state.get("company_size_edit",
                        self.company_profile.get("company_size", "Medium (51-200)"))
                    final_location = st.session_state.get("location_edit",
                        self.company_profile.get("location", ""))
                    final_location_type = st.session_state.get("location_type_edit",
                        self.company_profile.get("location_type", "Single Location"))
                    final_core_business = st.session_state.get("core_business_edit",
                        self.company_profile.get("core_business", ""))
                    final_target_customers = st.session_state.get("selected_customers_edit", 
                        self.company_profile.get("target_customers", []))
                    final_industries_served = st.session_state.get("selected_industries_edit",
                        self.company_profile.get("industries_served", []))
                    
                    if self._validate_form(final_company_name, final_core_business, final_target_customers, final_industries_served, products):
                        # Update the existing profile
                        updated_profile = {
                            "company_name": final_company_name,
                            "company_size": final_company_size,
                            "location": final_location,
                            "location_type": final_location_type,
                            "core_business": final_core_business,
                            "target_customers": final_target_customers,
                            "industries_served": final_industries_served,
                            "products": products,
                            "value_propositions": value_propositions,
                            "primary_color": primary_color,
                            "logo_url": logo_url,
                            "business_intelligence": {
                                "company_type": company_type,
                                "business_model": business_model,
                                "value_delivery_method": value_delivery_method,
                                "market_position": market_position,
                                "company_size": company_size_bi,
                                "maturity_stage": maturity_stage,
                                "geographic_scope": geographic_scope,
                                "industry_focus": industry_focus,
                                "revenue_model": revenue_model,
                                "customer_relationship_type": customer_relationship_type,
                                "innovation_focus": innovation_focus,
                                "competitive_advantage_type": competitive_advantage_type
                            },
                            "setup_complete": True,
                            "setup_date": datetime.now().isoformat(),  # Always use current time for updates
                            "company_id": self.company_profile.get("company_id", str(uuid.uuid4()))
                        }
                        
                        if self._save_company_profile(updated_profile):
                            st.success("✅ Company profile updated successfully!")
                            st.info("🔄 Changes have been applied to the application.")
                            
                            # Refresh the company context to load the updated profile
                            from app.core.company_context_manager import CompanyContextManager
                            company_context = CompanyContextManager()
                            company_context.refresh_profile()
                            
                            st.session_state.edit_company_profile = False
                            st.session_state.show_company_wizard = False
                            st.rerun()
                    else:
                        st.error("❌ Please fill in all required fields marked with *")
            
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.edit_company_profile = False
                    st.session_state.show_company_wizard = False
                    st.rerun()
    
    def _check_duplicate(self, new_value: str, existing_options: List[str], threshold: float = 0.85) -> tuple:
        """
        Check if a new value is a duplicate or very similar to existing options.
        Uses case-insensitive exact match and fuzzy string matching.
        
        Returns:
            (is_duplicate: bool, similar_option: str or None)
        """
        import difflib
        
        new_value_lower = new_value.lower().strip()
        new_value_normalized = ''.join(c for c in new_value_lower if c.isalnum() or c.isspace())
        
        # Check exact match (case-insensitive)
        for option in existing_options:
            if option.lower().strip() == new_value_lower:
                return True, option
        
        # Check fuzzy match (similarity)
        for option in existing_options:
            option_lower = option.lower().strip()
            option_normalized = ''.join(c for c in option_lower if c.isalnum() or c.isspace())
            
            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(None, new_value_normalized, option_normalized).ratio()
            
            if similarity >= threshold:
                return True, option
            
            # Also check if one contains the other (for typos like "end usersss" vs "end users")
            if len(new_value_normalized) > 3 and len(option_normalized) > 3:
                if new_value_normalized in option_normalized or option_normalized in new_value_normalized:
                    # Check if they're very similar in length (within 3 characters)
                    if abs(len(new_value_normalized) - len(option_normalized)) <= 3:
                        return True, option
        
        return False, None
    
    async def _process_customer_with_ai(self, custom_entry: str, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Process custom customer type with AI validation and fuzzy matching"""
        try:
            from app.ai.gemini_client import gemini_client
            
            # Standard options for fuzzy matching
            standard_options = [
                "OEMs (Original Equipment Manufacturers)", "Distributors", "End Users", 
                "System Integrators", "Resellers", "Consultants", "Other"
            ]
            
            # Simple fuzzy matching first
            custom_lower = custom_entry.lower()
            for option in standard_options:
                option_lower = option.lower()
                # Check if custom entry is similar to standard option
                if custom_lower in option_lower or option_lower in custom_lower:
                    return {
                        "is_valid": True,
                        "suggested_match": option,
                        "confidence": 0.9
                    }
                # Check for key words
                key_words = ["oem", "distributor", "end user", "system integrator", "reseller", "consultant"]
                for key_word in key_words:
                    if key_word in custom_lower and key_word in option_lower:
                        return {
                            "is_valid": True,
                            "suggested_match": option,
                            "confidence": 0.7
                        }
            
            # AI validation
            prompt = f"""
            Validate this customer type entry: "{custom_entry}"
            
            Company Context:
            - Core Business: {company_profile.get('core_business', 'N/A')}
            - Products: {company_profile.get('products', 'N/A')}
            - Business Model: {company_profile.get('business_intelligence', {}).get('business_model', 'N/A')}
            
            Standard Customer Types:
            - OEMs (Original Equipment Manufacturers)
            - Distributors
            - End Users
            - System Integrators
            - Resellers
            - Consultants
            
            Tasks:
            1. Check if "{custom_entry}" is a valid B2B customer type
            2. Suggest if it matches any standard option (fuzzy matching)
            3. If valid but not matching standard, confirm it's a valid custom customer type
            
            Return JSON only:
            {{
                "is_valid": true/false,
                "suggested_match": "standard option name or null",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation"
            }}
            """
            
            from app.config import GEMINI_MAX_TOKENS
            # Use config value but keep it reasonable for validation
            max_tokens = min(GEMINI_MAX_TOKENS, 2000)
            response = await gemini_client(prompt, temperature=0.2, max_tokens=max_tokens)
            
            # Parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    return result
            except:
                pass
            
            # Fallback: assume valid if AI doesn't reject it
            return {
                "is_valid": True,
                "suggested_match": None,
                "confidence": 0.5,
                "reasoning": "AI validation completed"
            }
            
        except Exception as e:
            logger.error(f"Error processing customer with AI: {e}")
            return {
                "is_valid": True,  # Allow manual entry even if AI fails
                "suggested_match": None,
                "confidence": 0.0
            }
    
    async def _process_industry_with_ai(self, custom_entry: str, company_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Process custom industry with AI validation and fuzzy matching"""
        try:
            from app.ai.gemini_client import gemini_client
            
            # Standard options for fuzzy matching
            standard_options = [
                "Mining", "Construction", "Agriculture", "Manufacturing", "Automotive",
                "Aerospace", "Marine", "Oil & Gas", "Utilities", "Other"
            ]
            
            # Simple fuzzy matching first
            custom_lower = custom_entry.lower()
            for option in standard_options:
                option_lower = option.lower()
                if custom_lower == option_lower:
                    return {
                        "is_valid": True,
                        "suggested_match": option,
                        "confidence": 1.0
                    }
                if custom_lower in option_lower or option_lower in custom_lower:
                    return {
                        "is_valid": True,
                        "suggested_match": option,
                        "confidence": 0.8
                    }
            
            # AI validation
            prompt = f"""
            Validate this industry entry: "{custom_entry}"
            
            Company Context:
            - Core Business: {company_profile.get('core_business', 'N/A')}
            - Products: {company_profile.get('products', 'N/A')}
            - Current Industries: {', '.join(company_profile.get('industries_served', []))}
            
            Standard Industries:
            - Mining, Construction, Agriculture, Manufacturing, Automotive
            - Aerospace, Marine, Oil & Gas, Utilities
            
            Tasks:
            1. Check if "{custom_entry}" is a valid industry
            2. Suggest if it matches any standard option (fuzzy matching)
            3. If valid but not matching standard, confirm it's a valid custom industry
            
            Return JSON only:
            {{
                "is_valid": true/false,
                "suggested_match": "standard option name or null",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation"
            }}
            """
            
            from app.config import GEMINI_MAX_TOKENS
            # Use config value but keep it reasonable for validation
            max_tokens = min(GEMINI_MAX_TOKENS, 2000)
            response = await gemini_client(prompt, temperature=0.2, max_tokens=max_tokens)
            
            # Parse JSON response
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    return result
            except:
                pass
            
            # Fallback: assume valid if AI doesn't reject it
            return {
                "is_valid": True,
                "suggested_match": None,
                "confidence": 0.5,
                "reasoning": "AI validation completed"
            }
            
        except Exception as e:
            logger.error(f"Error processing industry with AI: {e}")
            return {
                "is_valid": True,  # Allow manual entry even if AI fails
                "suggested_match": None,
                "confidence": 0.0
            }
    
    async def _get_ai_customer_suggestions(self, company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get AI suggestions for target customers based on company profile"""
        try:
            from app.ai.gemini_client import gemini_client
            from app.config import GEMINI_MAX_TOKENS
            
            # Truncate long fields to avoid token limits
            core_business = str(company_profile.get('core_business', 'N/A'))[:200]
            products = str(company_profile.get('products', 'N/A'))[:200]
            
            prompt = f"""Based on this company profile, suggest 5-7 relevant target customer types.

Company: {company_profile.get('company_name', 'N/A')}
Core Business: {core_business}
Products/Services: {products}
Business Model: {company_profile.get('business_intelligence', {}).get('business_model', 'N/A')}

Standard Options: OEMs, Distributors, End Users, System Integrators, Resellers, Consultants

Return ONLY a JSON array with this exact format:
[{{"name": "Customer Type", "confidence": 0.85, "reasoning": "Brief explanation"}}]"""
            
            # Use config value but ensure we have enough tokens for the response
            max_tokens = min(GEMINI_MAX_TOKENS, 4000)  # Cap at 4000 for suggestions
            response = await gemini_client(prompt, temperature=0.3, max_tokens=max_tokens)
            
            # Parse JSON response with better error handling
            try:
                import re
                # Try to find JSON array in response
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    # Check if response was truncated (common when hitting MAX_TOKENS)
                    if response.strip().endswith('...') or 'MAX_TOKENS' in str(response):
                        logger.warning("AI response was truncated, attempting to parse partial JSON")
                        # Try to fix incomplete JSON by closing brackets
                        if not json_str.strip().endswith(']'):
                            json_str = json_str.rstrip().rstrip(',') + ']'
                    suggestions = json.loads(json_str)
                    # Sort by confidence
                    suggestions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                    return suggestions[:7]  # Limit to 7 suggestions
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse AI suggestions JSON: {e}")
                logger.debug(f"Response was: {response[:500]}...")
            except Exception as e:
                logger.warning(f"Could not parse AI suggestions: {e}")
            
            # Fallback: return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting AI customer suggestions: {e}")
            return []
    
    async def _get_ai_industry_suggestions(self, company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get AI suggestions for industries based on company profile"""
        try:
            from app.ai.gemini_client import gemini_client
            from app.config import GEMINI_MAX_TOKENS
            
            # Truncate long fields to avoid token limits
            core_business = str(company_profile.get('core_business', 'N/A'))[:200]
            products = str(company_profile.get('products', 'N/A'))[:200]
            current_industries = ', '.join(company_profile.get('industries_served', []))[:150]
            
            prompt = f"""Based on this company profile, suggest 5-10 relevant industries.

Company: {company_profile.get('company_name', 'N/A')}
Core Business: {core_business}
Products/Services: {products}
Current Industries: {current_industries}
Industry Focus: {company_profile.get('business_intelligence', {}).get('industry_focus', 'N/A')}

Standard Options: Mining, Construction, Agriculture, Manufacturing, Automotive, Aerospace, Marine, Oil & Gas, Utilities

Return ONLY a JSON array with this exact format:
[{{"name": "Industry Name", "confidence": 0.87, "reasoning": "Brief explanation"}}]"""
            
            # Use config value but ensure we have enough tokens for the response
            max_tokens = min(GEMINI_MAX_TOKENS, 4000)  # Cap at 4000 for suggestions
            response = await gemini_client(prompt, temperature=0.3, max_tokens=max_tokens)
            
            # Parse JSON response with better error handling
            try:
                import re
                # Try to find JSON array in response
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    # Check if response was truncated (common when hitting MAX_TOKENS)
                    if response.strip().endswith('...') or 'MAX_TOKENS' in str(response):
                        logger.warning("AI response was truncated, attempting to parse partial JSON")
                        # Try to fix incomplete JSON by closing brackets
                        if not json_str.strip().endswith(']'):
                            json_str = json_str.rstrip().rstrip(',') + ']'
                    suggestions = json.loads(json_str)
                    # Sort by confidence
                    suggestions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                    return suggestions[:10]  # Limit to 10 suggestions
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse AI suggestions JSON: {e}")
                logger.debug(f"Response was: {response[:500]}...")
            except Exception as e:
                logger.warning(f"Could not parse AI suggestions: {e}")
            
            # Fallback: return empty list
            return []
            
        except Exception as e:
            logger.error(f"Error getting AI industry suggestions: {e}")
            return []
