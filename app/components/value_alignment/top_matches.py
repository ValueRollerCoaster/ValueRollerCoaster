import streamlit as st
import pandas as pd
from typing import Optional

def summarize_text(text, max_words=12):
    words = text.split()
    return ' '.join(words[:max_words]) + ('...' if len(words) > max_words else '')

def group_by_score(matches):
    high, medium, low = [], [], []
    for idx, item in enumerate(matches):
        score = item.get('match_score_percent', 0)
        if score >= 95:
            high.append((idx, item))
        elif 70 <= score < 95:
            medium.append((idx, item))
        else:
            low.append((idx, item))
    return high, medium, low

def render_top_matches(playbook_data: dict, selected_category: Optional[str] = None):
    alignment_matrix = playbook_data.get("alignment_matrix") or []
    if not alignment_matrix:
        st.info("No value alignment data available.")
        return None
    st.subheader("Value Alignment Matches")
    high, medium, low = group_by_score(alignment_matrix)
    col1, col2 = st.columns([0.35, 0.65])
    if 'selected_match_idx' not in st.session_state:
        st.session_state['selected_match_idx'] = None
    with col1:
        st.markdown("### High Alignment (≥ 95%)")
        if high:
            for idx, item in high:
                label = summarize_text(item.get('prospect_need') or item.get('customer_need', 'N/A'), 12)
                if st.button(label, key=f"high_{idx}"):
                    st.session_state['selected_match_idx'] = idx
        else:
            st.caption("No high alignment needs.")
        st.markdown("### Medium Alignment (94–70%)")
        if medium:
            for idx, item in medium:
                label = summarize_text(item.get('prospect_need') or item.get('customer_need', 'N/A'), 12)
                if st.button(label, key=f"medium_{idx}"):
                    st.session_state['selected_match_idx'] = idx
        else:
            st.caption("No medium alignment needs.")
        st.markdown("### Low Alignment (< 70%)")
        if low:
            for idx, item in low:
                label = summarize_text(item.get('prospect_need') or item.get('customer_need', 'N/A'), 12)
                if st.button(label, key=f"low_{idx}"):
                    st.session_state['selected_match_idx'] = idx
        else:
            st.caption("No low alignment needs.")
    with col2:
        idx = st.session_state.get('selected_match_idx')
        if idx is not None and 0 <= idx < len(alignment_matrix):
            item = alignment_matrix[idx]
            need = item.get('prospect_need') or item.get('customer_need', 'N/A')
            rationale = item.get('rationale', 'No rationale provided.')
            score = item.get('match_score_percent', 0)
            st.markdown(f"<div style='background:#f7f7fa;border-radius:10px;padding:1.5em 2em;margin-bottom:1em;box-shadow:0 1px 4px #0001;'>", unsafe_allow_html=True)
            st.markdown(f"**Customer Need / Goal:** <span style='color:#1976D2'>{need}</span>", unsafe_allow_html=True)
            st.markdown(f"**Matched Value Component:** <span style='color:#388E3C'>{item.get('our_value_component', 'N/A')}</span>", unsafe_allow_html=True)
            st.markdown(f"**Match Score:** <span style='color:#1976D2;font-weight:bold'>{score}%</span>", unsafe_allow_html=True)
            st.progress(score / 100)
            st.markdown(f"**Rationale:** {rationale}")
            conversation = item.get("conversation_starter")
            if conversation:
                st.info(f"💬 **Conversation Starter:** {conversation}")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Select a customer need from the left to view details.")
    return None 