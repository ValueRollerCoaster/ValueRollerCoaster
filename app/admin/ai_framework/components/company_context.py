"""
Company Context Component
Shows company profile data that influences framework generation
"""

import streamlit as st
from typing import Dict, Any

def render_company_context(company_profile: Dict[str, Any]) -> None:
    """Render company profile context that influences frameworks"""
    
    st.markdown("### 🏢 Company Profile Context")
    st.markdown("*Data from company profile that influences framework generation*")
    st.markdown("---")
    
    # Target Customers
    target_customers = company_profile.get("target_customers", [])
    if target_customers:
        st.markdown("**🎯 Target Customers:**")
        for customer in target_customers:
            st.markdown(f"• {customer}")
        st.caption("💡 Influences: Competitive Factors, Value Drivers")
    else:
        st.info("No target customers configured")
    
    st.markdown("---")
    
    # Industries Served
    industries_served = company_profile.get("industries_served", [])
    if industries_served:
        st.markdown("**🏭 Industries Served:**")
        for industry in industries_served:
            st.markdown(f"• {industry}")
        st.caption("💡 Influences: Pain Points, Trend Areas")
    else:
        st.info("No industries configured")
    
    st.markdown("---")
    
    # Core Business
    core_business = company_profile.get("core_business", "")
    if core_business:
        st.markdown("**💼 Core Business:**")
        st.text_area(
            "Core Business Description", 
            value=core_business, 
            height=100, 
            disabled=True, 
            key="core_business_display",
            label_visibility="hidden"
        )
        st.caption("💡 Influences: Value Drivers, Technology Focus, Competitive Factors")
    else:
        st.info("No core business description")
    
    st.markdown("---")
    
    # Products & Services
    products = company_profile.get("products", "")
    if products:
        st.markdown("**📦 Products & Services:**")
        st.text_area(
            "Products & Services Description", 
            value=products, 
            height=100, 
            disabled=True, 
            key="products_display",
            label_visibility="hidden"
        )
        st.caption("💡 Influences: Key Metrics")
    else:
        st.info("No products/services description")
    
    st.markdown("---")
    
    # Business Intelligence
    bi_data = company_profile.get("business_intelligence", {})
    if bi_data:
        st.markdown("**🧠 Business Intelligence:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Company Type:** {bi_data.get('company_type', 'N/A')}")
            st.markdown(f"**Business Model:** {bi_data.get('business_model', 'N/A')}")
            st.markdown(f"**Market Position:** {bi_data.get('market_position', 'N/A')}")
        
        with col2:
            st.markdown(f"**Value Delivery:** {bi_data.get('value_delivery_method', 'N/A')}")
            st.markdown(f"**Geographic Scope:** {bi_data.get('geographic_scope', 'N/A')}")
            st.markdown(f"**Industry Focus:** {bi_data.get('industry_focus', 'N/A')}")
        
        st.caption("💡 Influences: Framework customization and AI prompts")
    else:
        st.info("No business intelligence data configured")

