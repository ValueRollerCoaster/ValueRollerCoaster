import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from app.charts.technical_value_donut import technical_value_sunburst_chart
from app.charts.business_value_donut import business_value_sunburst_chart
from app.charts.strategic_value_donut import strategic_value_sunburst_chart
from app.charts.after_sales_value_donut import after_sales_value_sunburst_chart
from app.database import fetch_all_value_components
import hashlib
import json
from app.utils.spinner import ui_refresh_spinner

def render_distribution_tab(selected_main_category, value_components):
    st.subheader("📊 Distribution & Summary")
    
    with ui_refresh_spinner():
        # FIX: Get user_id using demo profile manager for proper data isolation
        from app.components.demo_companies.demo_profile_manager import demo_profile_manager
        user_id = demo_profile_manager.get_current_user_id()
        all_components = fetch_all_value_components(user_id=user_id)
    # Add a hash of the DB data to force chart refresh
    db_hash = hashlib.md5(json.dumps(all_components, sort_keys=True, default=str).encode()).hexdigest()
    # fetch_all_value_components always returns a Dict[str, List[Dict[str, Any]]]
    if isinstance(all_components, dict):
        filtered_components = all_components.get(selected_main_category.lower(), []) or []
    else:
        # Fallback for unexpected types
        filtered_components = []
    if isinstance(filtered_components, dict):
        filtered_components = list(filtered_components.values())

    chart = None
    if selected_main_category == "Technical Value":
        chart = technical_value_sunburst_chart(all_components, height=600, title_font_size=28)
    elif selected_main_category == "Business Value":
        chart = business_value_sunburst_chart(all_components, height=600, title_font_size=28)
    elif selected_main_category == "Strategic Value":
        chart = strategic_value_sunburst_chart(all_components, height=600, title_font_size=28)
    elif selected_main_category == "After Sales Value":
        chart = after_sales_value_sunburst_chart(all_components, height=600, title_font_size=28)
    if chart:
        st.plotly_chart(chart, use_container_width=True, key=f"donut_{selected_main_category}_summary_{db_hash}", config={"displayModeBar": True, "scrollZoom": True})
    st.markdown("---")
    st.subheader(f"{selected_main_category} Distribution Summary")
    st.markdown("""
    <div style='color:#555;font-size:1.05rem;'>
    This chart shows the distribution of value components for the selected category. The largest segments represent the most important or most frequently filled components. Use this view to quickly understand where your value proposition is strongest and where there may be gaps.
    </div>
    """, unsafe_allow_html=True) 