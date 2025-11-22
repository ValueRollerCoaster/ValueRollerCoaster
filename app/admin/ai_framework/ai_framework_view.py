"""
AI Framework View - Main Component
Provides transparency into industry framework generation and usage
"""

import streamlit as st
import logging
from typing import Dict, Any
from datetime import datetime

from .components.overview_dashboard import render_overview_dashboard
from .components.industry_frameworks import render_industry_frameworks
from .components.company_context import render_company_context

logger = logging.getLogger(__name__)

def render_ai_framework_view():
    """Main function to render the AI Framework admin view"""
    
    st.title("🤖 AI Framework")
    st.markdown("---")
    st.markdown("""
    **Transparency into Industry Framework Generation**
    
    This view shows how industry frameworks are dynamically generated based on your company profile 
    and how they're used to enhance AI-powered market intelligence and persona generation.
    """)
    st.markdown("---")
    
    try:
        # Load company profile
        from app.core.company_context_manager import CompanyContextManager
        company_context = CompanyContextManager()
        company_profile = company_context.get_company_profile()
        
        if not company_profile:
            st.error("❌ Company profile not found. Please set up your company profile first.")
            st.info("Go to **Company Profile** in the admin menu to configure your company.")
            return
        
        # Get framework generator
        from app.ai.market_intelligence.dynamic_generator import DynamicIndustryFrameworkGenerator
        framework_generator = DynamicIndustryFrameworkGenerator()
        
        # Get company industries
        company_industries = framework_generator.get_company_industries()
        
        if not company_industries:
            st.warning("⚠️ No industries configured in company profile.")
            st.info("Please add industries in your company profile to see framework generation.")
            return
        
        # Get frameworks (always without validation - validation is on-demand per framework)
        frameworks = framework_generator.get_company_frameworks()
        
        # Initialize validation results storage in session state if not exists
        if "framework_validations" not in st.session_state:
            st.session_state["framework_validations"] = {}
        
        # Main tabs
        tab1, tab2, tab3 = st.tabs([
            "📊 Overview Dashboard",
            "🏭 Industry Frameworks", 
            "🏢 Company Context"
        ])
        
        with tab1:
            # Level 1: Overview Dashboard
            render_overview_dashboard(frameworks, company_industries)
        
        with tab2:
            # Level 2 & 3: Industry Frameworks with details
            render_industry_frameworks(frameworks, company_profile, company_industries)
        
        with tab3:
            # Company Profile Context
            render_company_context(company_profile)
        
        # Footer with refresh option
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            # Show validation status from session state
            validated_count = sum(
                1 for industry in company_industries
                if industry in st.session_state.get("framework_validations", {})
                and st.session_state["framework_validations"][industry].get("overall_quality", 0) > 0
            )
            if validated_count > 0:
                st.caption(f"✅ {validated_count}/{len(frameworks)} frameworks validated")
        
        with col2:
            if st.button("🔄 Refresh All Frameworks", use_container_width=True):
                # Clear all framework cache
                if hasattr(framework_generator, 'framework_cache'):
                    framework_generator.framework_cache.clear()
                st.success("Framework cache cleared. Frameworks will regenerate on next use.")
                st.rerun()
        
        with col3:
            # Export option
            if st.button("📥 Export Data", use_container_width=True):
                import json
                export_data = {
                    "timestamp": datetime.now().isoformat(),
                    "company_industries": company_industries,
                    "frameworks": frameworks,
                    "company_profile_summary": {
                        "target_customers": company_profile.get("target_customers", []),
                        "industries_served": company_profile.get("industries_served", []),
                        "has_core_business": bool(company_profile.get("core_business")),
                        "has_products": bool(company_profile.get("products"))
                    }
                }
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"ai_framework_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
    except Exception as e:
        logger.error(f"Error rendering AI Framework view: {e}", exc_info=True)
        st.error(f"❌ Error loading AI Framework view: {str(e)}")
        st.info("Please ensure your company profile is properly configured.")

