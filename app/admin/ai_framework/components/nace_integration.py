"""
NACE Integration Component (Level 3 - Advanced)
Shows NACE code detection and insights
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def render_nace_integration(framework_data: Dict[str, Any], 
                           industry_name: str) -> None:
    """Render NACE system integration details"""
    
    st.markdown("### 📊 NACE System Integration")
    st.markdown("*European industry classification and insights*")
    st.markdown("---")
    
    # NACE Codes
    nace_codes = framework_data.get("nace_codes", [])
    
    if nace_codes:
        st.markdown("#### 🔢 Detected NACE Codes")
        
        for code in nace_codes:
            with st.expander(f"**NACE Code: {code}**", expanded=False):
                st.markdown(f"**Code:** {code}")
                st.markdown(f"**Industry:** {industry_name}")
                
                # Try to get NACE insights
                try:
                    from app.nace_system import NACE_System
                    nace_system = NACE_System()
                    insights = nace_system.get_industry_insights(code)
                    
                    if insights:
                        if insights.get("description"):
                            st.markdown(f"**Description:** {insights['description']}")
                        
                        if insights.get("trends"):
                            st.markdown("**Trends:**")
                            for trend in insights["trends"][:5]:
                                st.markdown(f"• {trend}")
                        
                        if insights.get("opportunities"):
                            st.markdown("**Opportunities:**")
                            for opp in insights["opportunities"][:5]:
                                st.markdown(f"• {opp}")
                    else:
                        st.info("No additional insights available for this NACE code")
                except Exception as e:
                    st.warning(f"Could not load NACE insights: {e}")
        
        st.markdown("---")
        
        # NACE System Status
        st.markdown("#### ✅ NACE System Status")
        st.success(f"NACE system is active. {len(nace_codes)} code(s) detected for {industry_name}.")
        
    else:
        st.warning("⚠️ No NACE codes detected for this industry")
        st.info("""
        **Why no NACE codes?**
        - Industry name might not match NACE classification
        - NACE system might be unavailable
        - Industry might be too specific or new
        
        Framework will still work using generic industry data.
        """)
    
    st.markdown("---")
    
    # NACE Code Detection Process
    st.markdown("#### 🔍 NACE Detection Process")
    
    st.markdown("""
    **How NACE codes are detected:**
    1. Industry name is normalized and matched against NACE classification
    2. Primary NACE code is identified
    3. Related NACE codes are retrieved
    4. NACE insights (trends, opportunities) are loaded
    
    **Impact on Framework:**
    - NACE codes enhance trend areas
    - NACE opportunities inform value drivers
    - NACE insights provide industry-specific context
    """)
    
    # Try to show detection result
    try:
        from app.nace_system import NACE_System
        nace_system = NACE_System()
        detection_result = nace_system.detect_industry_nace(industry_name)
        
        if detection_result:
            with st.expander("🔬 Detection Details", expanded=False):
                st.json(detection_result)
    except Exception as e:
        logger.debug(f"NACE detection details unavailable: {e}")

