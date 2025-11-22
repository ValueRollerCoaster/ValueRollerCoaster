import streamlit as st

def render_opportunities(playbook_data: dict, selected_category: str):
    unmatched_needs = playbook_data.get("unmatched_needs") or []
    if not unmatched_needs:
        return
    st.subheader("Opportunities (Unmatched Needs)")
    for need in unmatched_needs:
        st.markdown(f"<span style='background:#FFC107;color:#333;border-radius:16px;padding:0.4em 1em;margin:0.2em 0.3em;display:inline-block;font-size:1.05em;'>{need}</span>", unsafe_allow_html=True)
    st.info("Consider addressing these needs to improve your value alignment.") 