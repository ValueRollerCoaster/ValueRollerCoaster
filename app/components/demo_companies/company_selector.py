"""
Demo Company Selector
Interactive dropdown for selecting demo companies
"""

import streamlit as st
from typing import Dict, Any, Optional
from .company_data import get_company_display_info, get_company_by_id

def render_company_selector() -> Optional[str]:
    """
    Render the demo company selector dropdown
    Returns the selected company ID or None
    """
    st.markdown("### 🎭 Choose Your Demo")
    st.markdown("Select a funny company to populate your value components with realistic demo data!")
    
    # Get company display information
    companies = get_company_display_info()
    
    if not companies:
        st.error("No demo companies available")
        return None
    
    # Create dropdown options
    options = [company['name'] for company in companies]
    company_ids = [company['id'] for company in companies]
    
    # Create the selector
    selected_index = st.selectbox(
        "Select a Demo Company:",
        range(len(options)),
        format_func=lambda x: options[x],
    )
    
    if selected_index is not None:
        selected_company_id = company_ids[selected_index]
        selected_company = get_company_by_id(selected_company_id)
        
        if selected_company:
            # Display short company description on blue background
            company_name = selected_company['company_name']
            core_business = selected_company['core_business']
            demo_customers_count = len(selected_company.get('demo_customers', []))
            
            st.markdown("---")
            st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 1em; border-radius: 8px; border-left: 4px solid #2196f3;'>
                <strong>🎭 {company_name}</strong><br>
                {core_business}<br>
                <em>Includes {demo_customers_count} demo customers for persona generation.</em>
            </div>
            """, unsafe_allow_html=True)
            
            # Add additional whitespace
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            return selected_company_id
    
    return None

def render_company_selector_with_preview() -> Optional[Dict[str, Any]]:
    """
    Render the demo company selector with full company data preview
    Returns the selected company data or None
    """
    st.markdown("### 🎭 Choose Your Demo")
    st.markdown("Select a funny company to populate your value components with realistic demo data!")
    
    # Get company display information
    companies = get_company_display_info()
    
    if not companies:
        st.error("No demo companies available")
        return None
    
    # Create dropdown options
    options = [company['name'] for company in companies]
    company_ids = [company['id'] for company in companies]
    
    # Create the selector
    selected_index = st.selectbox(
        "Select a Demo Company:",
        range(len(options)),
        format_func=lambda x: options[x],
    )
    
    if selected_index is not None:
        selected_company_id = company_ids[selected_index]
        selected_company = get_company_by_id(selected_company_id)
        
        if selected_company:
            # Display company preview
            st.markdown("---")
            st.markdown(f"**Selected Company:** {selected_company['company_name']}")
            st.markdown(f"**Business:** {selected_company['core_business']}")
            st.markdown(f"**Size:** {selected_company['company_size']}")
            st.markdown(f"**Location:** {selected_company['location']}")
            
            # Show demo customers preview
            demo_customers = selected_company.get('demo_customers', [])
            if demo_customers:
                st.markdown("**Demo Customers Available:**")
                for i, customer in enumerate(demo_customers, 1):
                    st.markdown(f"{i}. **{customer['company_name']}** - {customer['description']}")
            
            return selected_company
    
    return None

def render_company_selector_compact() -> Optional[str]:
    """
    Render a compact version of the demo company selector
    Returns the selected company ID or None
    """
    # Get company display information
    companies = get_company_display_info()
    
    if not companies:
        st.error("No demo companies available")
        return None
    
    # Create dropdown options
    options = [f"{company['name']}" for company in companies]
    company_ids = [company['id'] for company in companies]
    
    # Create the selector
    selected_index = st.selectbox(
        "Select Demo Company:",
        range(len(options)),
        format_func=lambda x: options[x],
        help="Choose a demo company to populate your value components"
    )
    
    if selected_index is not None:
        return company_ids[selected_index]
    
    return None
