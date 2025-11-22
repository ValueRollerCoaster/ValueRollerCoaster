"""
Prompt Flow Component (Level 3 - Advanced)
Shows how framework data flows into AI prompts
"""

import streamlit as st
from typing import Dict, Any
from ..utils.framework_helpers import format_framework_context_for_display, estimate_prompt_tokens

def render_prompt_flow(framework_data: Dict[str, Any], 
                      company_profile: Dict[str, Any],
                      industry_name: str) -> None:
    """Render framework-to-prompt flow visualization"""
    
    st.markdown("### 🔄 Framework-to-Prompt Flow")
    st.markdown("*How framework data is used in AI prompts*")
    st.markdown("---")
    
    # Framework Context Preview
    st.markdown("#### 📋 Framework Context (as used in prompts)")
    
    framework_context = format_framework_context_for_display(framework_data)
    
    with st.expander("View Framework Context", expanded=True):
        st.code(framework_context, language="text")
        
        # Token estimation
        estimated_tokens = estimate_prompt_tokens(framework_context)
        st.caption(f"Estimated tokens: ~{estimated_tokens}")
    
    st.markdown("---")
    
    # Prompt Structure
    st.markdown("#### 📝 Prompt Structure")
    
    st.markdown("""
    When generating market intelligence, the framework context is embedded in the prompt like this:
    """)
    
    example_prompt = f"""
You are a senior market intelligence analyst with expertise in {industry_name} industry.

INDUSTRY FRAMEWORK:
{framework_context}

COMPANY CONTEXT: [Company summary with core business, products, target customers]

Please provide comprehensive market intelligence analysis...
"""
    
    with st.expander("Example Prompt Structure", expanded=False):
        st.code(example_prompt, language="text")
        st.caption(f"Total estimated tokens: ~{estimate_prompt_tokens(example_prompt)}")
    
    st.markdown("---")
    
    # Framework Property Mapping
    st.markdown("#### 🗺️ Framework → Market Intelligence Mapping")
    
    mapping_data = {
        "Trend Areas": "→ Current Trends in market intelligence",
        "Value Drivers": "→ Market Opportunities & Strategic Recommendations",
        "Pain Points": "→ Risk Factors",
        "Competitive Factors": "→ Competitive Landscape",
        "Technology Focus": "→ Technology Adoption section",
        "Sustainability Initiatives": "→ Sustainability Initiatives section",
        "Key Metrics": "→ Market Overview & Analysis focus areas",
        "NACE Codes": "→ Industry classification & NACE insights"
    }
    
    for framework_prop, intelligence_section in mapping_data.items():
        st.markdown(f"**{framework_prop}** {intelligence_section}")
    
    st.markdown("---")
    
    # Usage Statistics
    st.markdown("#### 📊 Framework Usage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Framework Properties:**")
        st.markdown(f"• Total properties: 9")
        st.markdown(f"• Properties with data: {sum(1 for key in ['nace_codes', 'key_metrics', 'trend_areas', 'competitive_factors', 'value_drivers', 'pain_points', 'technology_focus', 'sustainability_initiatives'] if framework_data.get(key))}")
        st.markdown(f"• Total items across all properties: {sum(len(framework_data.get(key, [])) if isinstance(framework_data.get(key), list) else 1 for key in framework_data.keys() if key != 'industry_name')}")
    
    with col2:
        st.markdown("**Prompt Integration:**")
        st.markdown(f"• Framework context tokens: ~{estimate_prompt_tokens(framework_context)}")
        st.markdown(f"• Used in: Market Intelligence generation")
        st.markdown(f"• Used in: Value Alignment prompts")
        st.markdown(f"• Used in: Persona generation")

