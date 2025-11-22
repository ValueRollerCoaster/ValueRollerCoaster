"""
Demo Customer Selector Component
Allows users to select from generated demo customers for persona generation
"""

import streamlit as st
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def render_demo_customer_selector() -> Optional[str]:
    """Render demo customer selector and return selected website"""
    try:
        # Check if demo customers are available
        demo_customers = st.session_state.get("demo_customers", [])
        
        if not demo_customers:
            return None
        
        st.markdown("### 🎭 Demo Customers")
        st.markdown("Select a demo customer to generate a persona:")
        
        # Create customer options
        customer_options = []
        for i, customer in enumerate(demo_customers):
            company_name = customer.get("company_name", f"Customer {i+1}")
            industry = customer.get("industry", "Unknown")
            size = customer.get("size", "Unknown")
            website = customer.get("website", "")
            customer_id = customer.get("id", f"customer_{i+1}")
            
            option_text = f"{company_name} ({industry}, {size})"
            customer_options.append((option_text, customer_id, website))
        
        # Add "Custom Website" option
        customer_options.append(("🌐 Enter Custom Website", "custom", "custom"))
        
        # Create selectbox
        selected_option = st.selectbox(
            "Choose a demo customer:",
            options=[opt[0] for opt in customer_options],
            index=0,
            key="demo_customer_selector"
        )
        
        # Get selected customer info
        selected_customer_id = None
        selected_website = None
        for option_text, customer_id, website in customer_options:
            if option_text == selected_option:
                selected_customer_id = customer_id
                selected_website = website
                break
        
        # Handle custom website input
        if selected_website == "custom":
            st.markdown("---")
            st.markdown("### 🌐 Custom Website")
            custom_website = st.text_input(
                "Enter website URL:",
                placeholder="https://example.com",
                key="custom_website_input"
            )
            if custom_website:
                selected_website = custom_website
                selected_customer_id = None
        
        # Show selected customer info
        if selected_website and selected_website != "custom":
            selected_customer = None
            for customer in demo_customers:
                if customer.get("website") == selected_website:
                    selected_customer = customer
                    break
            
            if selected_customer:
                st.markdown("---")
                st.markdown("### 📋 Selected Customer Info")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Company:** {selected_customer.get('company_name', 'N/A')}")
                    st.markdown(f"**Industry:** {selected_customer.get('industry', 'N/A')}")
                    st.markdown(f"**Size:** {selected_customer.get('size', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Location:** {selected_customer.get('location', 'N/A')}")
                    st.markdown(f"**Website:** {selected_customer.get('website', 'N/A')}")
                
                # Show pain points and goals
                pain_points = selected_customer.get('pain_points', [])
                if pain_points:
                    st.markdown("**Pain Points:**")
                    for point in pain_points:
                        st.markdown(f"- {point}")
                
                goals = selected_customer.get('goals', [])
                if goals:
                    st.markdown("**Goals:**")
                    for goal in goals:
                        st.markdown(f"- {goal}")
        
        # Return demo:// format for demo customers, regular website for custom
        if selected_customer_id and selected_customer_id != "custom":
            return f"demo://{selected_customer_id}"
        else:
            return selected_website
        
    except Exception as e:
        logger.error(f"Error rendering demo customer selector: {e}")
        return None

def get_demo_customer_info(website: str) -> Dict[str, Any]:
    """Get demo customer info for a specific website"""
    try:
        demo_customers = st.session_state.get("demo_customers", [])
        for customer in demo_customers:
            if customer.get("website") == website:
                return customer
        return {}
    except Exception as e:
        logger.error(f"Error getting demo customer info: {e}")
        return {}

def render_demo_customer_summary():
    """Render summary of available demo customers"""
    try:
        demo_customers = st.session_state.get("demo_customers", [])
        
        if not demo_customers:
            return
        
        st.markdown("### 🎭 Available Demo Customers")
        
        for i, customer in enumerate(demo_customers):
            with st.expander(f"{customer.get('company_name', f'Customer {i+1}')} - {customer.get('industry', 'Unknown')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Company:** {customer.get('company_name', 'N/A')}")
                    st.markdown(f"**Industry:** {customer.get('industry', 'N/A')}")
                    st.markdown(f"**Size:** {customer.get('size', 'N/A')}")
                    st.markdown(f"**Location:** {customer.get('location', 'N/A')}")
                
                with col2:
                    st.markdown(f"**Website:** {customer.get('website', 'N/A')}")
                    
                    pain_points = customer.get('pain_points', [])
                    if pain_points:
                        st.markdown("**Pain Points:**")
                        for point in pain_points:
                            st.markdown(f"- {point}")
                
                goals = customer.get('goals', [])
                if goals:
                    st.markdown("**Goals:**")
                    for goal in goals:
                        st.markdown(f"- {goal}")
                
                value_drivers = customer.get('value_drivers', [])
                if value_drivers:
                    st.markdown("**Value Drivers:**")
                    for driver in value_drivers:
                        st.markdown(f"- {driver}")
        
    except Exception as e:
        logger.error(f"Error rendering demo customer summary: {e}")
