"""
Industry Frameworks Component (Level 2 - Standard)
Shows framework details for selected industry
"""

import streamlit as st
import logging
from typing import Dict, Any
from .framework_properties import render_framework_properties
from .prompt_flow import render_prompt_flow
from .nace_integration import render_nace_integration

logger = logging.getLogger(__name__)

def render_industry_frameworks(frameworks: Dict[str, Dict[str, Any]], 
                               company_profile: Dict[str, Any],
                               company_industries: list) -> None:
    """Render industry frameworks with selection and details"""
    
    st.markdown("### 🏭 Industry Frameworks")
    st.markdown("---")
    
    if not frameworks:
        st.warning("No frameworks generated yet. Frameworks are created automatically based on your company profile.")
        return
    
    # Industry Selector
    industry_options = {}
    for normalized_name, framework_data in frameworks.items():
        display_name = framework_data.get("industry_name", normalized_name.title())
        industry_options[display_name] = normalized_name
    
    if not industry_options:
        st.info("No industries available. Please configure your company profile.")
        return
    
    selected_display = st.selectbox(
        "Select Industry to View Framework:",
        options=list(industry_options.keys()),
        key="framework_industry_selector"
    )
    
    selected_normalized = industry_options[selected_display]
    # Use framework from session state if available (for edited frameworks), otherwise use original
    selected_framework = st.session_state.get(f"framework_data_{selected_normalized}", frameworks[selected_normalized])
    
    st.markdown("---")
    
    # Framework Header with Validation Button
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f"#### 🏭 {selected_display} Framework")
    
    with col2:
        if st.button("🔄 Refresh Framework", key=f"refresh_{selected_normalized}", use_container_width=True):
            # Clear cache for this industry
            from app.ai.market_intelligence.dynamic_generator import DynamicIndustryFrameworkGenerator
            generator = DynamicIndustryFrameworkGenerator()
            if hasattr(generator, 'framework_cache'):
                if selected_normalized in generator.framework_cache:
                    del generator.framework_cache[selected_normalized]
            # Also clear validation if exists
            if "framework_validations" in st.session_state:
                if selected_normalized in st.session_state["framework_validations"]:
                    del st.session_state["framework_validations"][selected_normalized]
            st.success("Framework cache cleared. Framework will regenerate on next use.")
            st.rerun()
    
    with col3:
        # Validate Framework button
        validation_key = f"validate_{selected_normalized}"
        has_validation = (
            "framework_validations" in st.session_state and
            selected_normalized in st.session_state["framework_validations"] and
            st.session_state["framework_validations"][selected_normalized].get("overall_quality", 0) > 0
        )
        
        if has_validation:
            validation = st.session_state["framework_validations"][selected_normalized]
            quality = validation.get("overall_quality", 0)
            if quality >= 80:
                button_label = "✅ Validated"
                button_type = "primary"
            elif quality >= 60:
                button_label = "⚠️ Validated"
                button_type = "secondary"
            else:
                button_label = "❌ Validated"
                button_type = "secondary"
        else:
            button_label = "🔍 Validate"
            button_type = "primary"
        
        if st.button(button_label, key=validation_key, use_container_width=True, type=button_type):
            # Trigger validation for this framework
            import asyncio
            from app.ai.market_intelligence.validation.framework_validator import FrameworkValidator
            from app.core.company_context_manager import CompanyContextManager
            
            with st.spinner(f"🔄 Validating {selected_display} framework... This may take a minute."):
                try:
                    # Get framework to validate (use edited version from session state if available)
                    framework_to_validate = st.session_state.get(f"framework_data_{selected_normalized}", selected_framework)
                    
                    # Get validated framework
                    
                    company_context = CompanyContextManager()
                    company_profile = company_context.get_company_profile()
                    
                    validator = FrameworkValidator(company_profile)
                    validation_results = asyncio.run(validator.validate(framework_to_validate, selected_normalized))
                    
                    # Create validated framework structure
                    validated_framework = framework_to_validate.copy()
                    validated_framework["_validation"] = validation_results
                    
                    # Store validation results in session state
                    if "framework_validations" not in st.session_state:
                        st.session_state["framework_validations"] = {}
                    
                    if "_validation" in validated_framework:
                        # Store previous validation for comparison if exists
                        if selected_normalized in st.session_state["framework_validations"]:
                            st.session_state[f"prev_validation_{selected_normalized}"] = st.session_state["framework_validations"][selected_normalized]
                        
                        st.session_state["framework_validations"][selected_normalized] = validated_framework["_validation"]
                        quality = validated_framework['_validation'].get('overall_quality', 0)
                        st.success(f"✅ Framework validated! Quality score: {quality:.1f}/100")
                        
                        # Show comparison if previous validation exists
                        prev_validation = st.session_state.get(f"prev_validation_{selected_normalized}")
                        if prev_validation:
                            prev_quality = prev_validation.get("overall_quality", 0)
                            improvement = quality - prev_quality
                            if improvement > 0:
                                st.success(f"📈 Quality improved by {improvement:.1f} points!")
                            elif improvement < 0:
                                st.warning(f"📉 Quality changed by {improvement:.1f} points")
                    else:
                        st.warning("⚠️ Validation completed but no results returned.")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Validation failed: {str(e)}")
                    logger.error(f"Validation error for {selected_normalized}: {e}", exc_info=True)
    
    with col4:
        # Framework status
        nace_codes = selected_framework.get("nace_codes", [])
        if nace_codes:
            st.success(f"✅ {len(nace_codes)} NACE")
        else:
            st.warning("⚠️ No NACE")
    
    st.markdown("---")
    
    # Check if validation exists for this framework
    has_validation = (
        "framework_validations" in st.session_state and
        selected_normalized in st.session_state["framework_validations"]
    )
    
    # Store framework reference in session state for editing
    st.session_state[f"framework_data_{selected_normalized}"] = selected_framework
    
    # Merge validation into framework data for display
    if has_validation:
        selected_framework = selected_framework.copy()
        selected_framework["_validation"] = st.session_state["framework_validations"][selected_normalized]
    
    # Framework Properties (Level 2)
    st.markdown("#### 📋 Framework Properties")
    st.markdown("*Expand each section to see detailed framework data*")
    
    render_framework_properties(selected_framework, company_profile, selected_normalized, has_validation)
    
    st.markdown("---")
    
    # Advanced Sections (Level 3)
    st.markdown("### 🔬 Advanced Details")
    
    # Tabs for advanced sections
    tab1, tab2 = st.tabs(["🔄 Prompt Flow", "📊 NACE Integration"])
    
    with tab1:
        render_prompt_flow(selected_framework, company_profile, selected_display)
    
    with tab2:
        render_nace_integration(selected_framework, selected_display)
    
    st.markdown("---")
    
    # Framework Metadata
    with st.expander("📊 Framework Metadata", expanded=False):
        st.markdown("**Framework Generation Info:**")
        st.markdown(f"• Industry: {selected_display}")
        st.markdown(f"• Normalized Name: {selected_normalized}")
        st.markdown(f"• NACE Codes: {len(nace_codes)}")
        st.markdown(f"• Key Metrics: {len(selected_framework.get('key_metrics', []))}")
        st.markdown(f"• Trend Areas: {len(selected_framework.get('trend_areas', []))}")
        st.markdown(f"• Value Drivers: {len(selected_framework.get('value_drivers', []))}")
        st.markdown(f"• Pain Points: {len(selected_framework.get('pain_points', []))}")
        st.markdown(f"• Technology Focus: {len(selected_framework.get('technology_focus', []))}")
        st.markdown(f"• Sustainability: {len(selected_framework.get('sustainability_initiatives', []))}")
        
        # Raw framework data (JSON)
        st.markdown("**Raw Framework Data (JSON):**")
        import json
        st.json(selected_framework)

