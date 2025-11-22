from app.categories import COMPONENT_STRUCTURES
import streamlit as st

def render_value_components_header(selected_main_category):
    st.markdown(f"""
        <div style='margin-bottom:1.5em;'>
            <div style='font-size:2rem;font-weight:600;display:flex;align-items:center;'>
                <span style='font-size:2.2rem;margin-right:0.5em;'>{COMPONENT_STRUCTURES[selected_main_category]['icon']}</span> {selected_main_category}
            </div>
            <div style='color:#888;font-size:1.1rem;margin-top:0.2em;'>{COMPONENT_STRUCTURES[selected_main_category]['description']}</div>
        </div>
    """, unsafe_allow_html=True) 