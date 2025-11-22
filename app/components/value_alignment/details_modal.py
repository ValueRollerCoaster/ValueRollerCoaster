import streamlit as st

def render_details_modal(selected_alignment: dict):
    with st.expander("Alignment Details", expanded=True):
        st.markdown(f"**Customer Need / Goal:** <span style='color:#1976D2'>{selected_alignment.get('prospect_need') or selected_alignment.get('customer_need', 'N/A')}</span>", unsafe_allow_html=True)
        st.markdown(f"**Matched Value Component:** <span style='color:#388E3C'>{selected_alignment.get('our_value_component', 'N/A')}</span>", unsafe_allow_html=True)
        match_score = selected_alignment.get("match_score_percent")
        rationale = selected_alignment.get("rationale", "No rationale provided.")
        conversation = selected_alignment.get("conversation_starter")
        if match_score is not None:
            st.markdown(f"**Match Score:** <span style='color:#1976D2;font-weight:bold'>{match_score}%</span>", unsafe_allow_html=True)
            st.progress(match_score / 100)
        st.markdown(f"**Rationale:** {rationale}")
        if conversation:
            st.info(f"💬 **Conversation Starter:** {conversation}") 