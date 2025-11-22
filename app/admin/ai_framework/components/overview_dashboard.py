"""
Overview Dashboard Component (Level 1)
Shows summary statistics and industry list
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
from ..utils.framework_helpers import get_framework_summary_stats

def render_overview_dashboard(frameworks: Dict[str, Dict[str, Any]], 
                             company_industries: list) -> None:
    """Render the overview dashboard with summary statistics"""
    
    st.markdown("### 📊 Framework Overview Dashboard")
    st.markdown("---")
    
    # Calculate summary statistics
    stats = get_framework_summary_stats(frameworks)
    
    # Add quality statistics if validation data exists in session state
    frameworks_with_validation = frameworks  # Default to original frameworks
    validation_enabled = False
    if "framework_validations" in st.session_state and st.session_state["framework_validations"]:
        # Merge validation data into frameworks for stats calculation
        frameworks_with_validation = {}
        for industry, framework in frameworks.items():
            framework_copy = framework.copy()
            if industry in st.session_state["framework_validations"]:
                framework_copy["_validation"] = st.session_state["framework_validations"][industry]
            frameworks_with_validation[industry] = framework_copy
        quality_stats = _calculate_quality_stats(frameworks_with_validation)
        stats.update(quality_stats)
        validation_enabled = True
    
    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Industries",
            value=stats["total_industries"],
            help="Number of industries with generated frameworks"
        )
    
    with col2:
        if validation_enabled and "avg_quality" in stats:
            st.metric(
                label="Avg Quality Score",
                value=f"{stats['avg_quality']:.1f}/100",
                delta=f"{stats['avg_quality'] - 70:.1f}" if stats['avg_quality'] > 70 else None,
                delta_color="normal",
                help="Average framework quality score across all industries"
            )
        else:
            st.metric(
                label="NACE Coverage",
                value=f"{stats['nace_coverage']:.0f}%",
                help="Percentage of industries with NACE codes detected"
            )
    
    with col3:
        st.metric(
            label="Avg Key Metrics",
            value=stats["avg_metrics"],
            help="Average number of key metrics per industry"
        )
    
    with col4:
        st.metric(
            label="Total NACE Codes",
            value=stats["total_nace_codes"],
            help="Total number of NACE codes across all industries"
        )
    
    st.markdown("---")
    
    # Quality Dashboard (if validation enabled)
    if validation_enabled:
        _render_quality_dashboard(frameworks_with_validation)
        st.markdown("---")
    
    # Additional Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Avg Trend Areas",
            value=stats["avg_trends"],
            help="Average number of trend areas per industry"
        )
    
    with col2:
        st.metric(
            label="Avg Value Drivers",
            value=stats["avg_value_drivers"],
            help="Average number of value drivers per industry"
        )
    
    with col3:
        # Framework generation status
        if frameworks:
            if validation_enabled:
                # Check validation status from session state
                validated = sum(
                    1 for industry in company_industries
                    if industry in st.session_state.get("framework_validations", {})
                    and st.session_state["framework_validations"][industry].get("overall_quality", 0) > 0
                )
                if validated == len(frameworks):
                    status = "✅ All Validated"
                    status_color = "green"
                elif validated > 0:
                    status = f"⚠️ {validated}/{len(frameworks)} Validated"
                    status_color = "orange"
                else:
                    status = "❌ Not Validated"
                    status_color = "red"
            else:
                status = "✅ All Generated"
                status_color = "green"
        else:
            status = "⚠️ No Frameworks"
            status_color = "orange"
        
        st.markdown(f"**Status:** <span style='color: {status_color}'>{status}</span>", 
                   unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Industry List
    st.markdown("### 🏭 Company Industries")
    
    if company_industries:
        # Display industries in a grid
        cols = st.columns(min(3, len(company_industries)))
        for idx, industry in enumerate(company_industries):
            with cols[idx % 3]:
                framework_data = frameworks.get(industry, {})
                industry_name = framework_data.get("industry_name", industry.title())
                
                # Status indicator
                if framework_data:
                    nace_codes = framework_data.get("nace_codes", [])
                    validation = framework_data.get("_validation", {})
                    
                    # Quality indicator (if validation exists in session state)
                    if (
                        "framework_validations" in st.session_state and
                        industry in st.session_state["framework_validations"] and
                        st.session_state["framework_validations"][industry].get("overall_quality", 0) > 0
                    ):
                        quality = st.session_state["framework_validations"][industry]["overall_quality"]
                        if quality >= 80:
                            quality_icon = "🟢"
                            quality_text = f"Quality: {quality:.0f}/100"
                        elif quality >= 60:
                            quality_icon = "🟡"
                            quality_text = f"Quality: {quality:.0f}/100"
                        else:
                            quality_icon = "🔴"
                            quality_text = f"Quality: {quality:.0f}/100"
                    else:
                        quality_icon = ""
                        quality_text = ""
                    
                    if nace_codes:
                        status_icon = "✅"
                        status_text = f"{len(nace_codes)} NACE code(s)"
                    else:
                        status_icon = "⚠️"
                        status_text = "No NACE codes"
                else:
                    status_icon = "❌"
                    status_text = "No framework"
                    quality_icon = ""
                    quality_text = ""
                
                st.markdown(f"""
                <div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;'>
                    <strong>{status_icon} {industry_name}</strong><br>
                    <small style='color: #666'>{status_text}</small>
                    {f'<br><small style="color: #666">{quality_icon} {quality_text}</small>' if quality_text else ''}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No industries configured in company profile. Please set up your company profile first.")
    
    st.markdown("---")

def _calculate_quality_stats(frameworks: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate quality statistics from validation results"""
    quality_scores = []
    for fw in frameworks.values():
        validation = fw.get("_validation", {})
        quality = validation.get("overall_quality", 0)
        if quality > 0:
            quality_scores.append(quality)
    
    if quality_scores:
        return {
            "avg_quality": sum(quality_scores) / len(quality_scores),
            "min_quality": min(quality_scores),
            "max_quality": max(quality_scores),
            "validated_count": len(quality_scores)
        }
    return {
        "avg_quality": 0,
        "min_quality": 0,
        "max_quality": 0,
        "validated_count": 0
    }

def _render_quality_dashboard(frameworks: Dict[str, Dict[str, Any]]) -> None:
    """Render quality dashboard section"""
    st.markdown("### 📈 Framework Quality Dashboard")
    
    # Collect all quality data
    quality_data = []
    for industry, fw_data in frameworks.items():
        validation = fw_data.get("_validation", {})
        if validation.get("overall_quality", 0) > 0:
            quality_data.append({
                "industry": fw_data.get("industry_name", industry),
                "overall": validation.get("overall_quality", 0),
                "relevance": _get_avg_relevance(validation),
                "completeness": validation.get("completeness", {}).get("completeness_score", 0),
                "consistency": validation.get("consistency", {}).get("consistency_score", 0)
            })
    
    if not quality_data:
        st.info("No validation data available. Enable validation to see quality scores.")
        return
    
    # Display quality metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_overall = sum(d["overall"] for d in quality_data) / len(quality_data)
        st.metric("Avg Overall Quality", f"{avg_overall:.1f}/100")
    
    with col2:
        avg_relevance = sum(d["relevance"] for d in quality_data) / len(quality_data)
        st.metric("Avg Relevance", f"{avg_relevance:.1f}/100")
    
    with col3:
        avg_completeness = sum(d["completeness"] for d in quality_data) / len(quality_data)
        st.metric("Avg Completeness", f"{avg_completeness:.1f}/100")
    
    with col4:
        avg_consistency = sum(d["consistency"] for d in quality_data) / len(quality_data)
        st.metric("Avg Consistency", f"{avg_consistency:.1f}/100")
    
    # Quality by industry table
    st.markdown("#### Quality by Industry")
    df = pd.DataFrame(quality_data)
    st.dataframe(
        df[["industry", "overall", "relevance", "completeness", "consistency"]].round(1),
        use_container_width=True,
        hide_index=True
    )

def _get_avg_relevance(validation: Dict[str, Any]) -> float:
    """Get average relevance score"""
    relevance = validation.get("relevance", {})
    if isinstance(relevance, dict):
        scores = [
            r.get("property_score", 0) 
            for r in relevance.values() 
            if isinstance(r, dict)
        ]
        if scores:
            return sum(scores) / len(scores)
    return 0.0

