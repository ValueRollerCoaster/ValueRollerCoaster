import streamlit as st
import pandas as pd
from statistics import mean
try:
    import plotly.graph_objects as go
except ImportError:
    go = None

def summarize_text(text, max_words=5):
    words = text.split()
    return ' '.join(words[:max_words]) + ('...' if len(words) > max_words else '')

def render_summary_bar(playbook_data: dict):
    alignment_matrix = playbook_data.get("alignment_matrix") or []
    if not alignment_matrix:
        st.info("No value alignment data available.")
        return
    num_matches = len(alignment_matrix)
    avg_score = mean([item.get("match_score_percent", 0) for item in alignment_matrix]) if alignment_matrix else 0
    num_gaps = sum(1 for item in alignment_matrix if (item.get("match_score_percent") or 0) < 50)
    st.markdown("<div style='display:flex;gap:2em;align-items:center;margin-bottom:1em;max-width:900px;margin:auto;'>" \
        f"<span style='background:#1976D2;color:#fff;border-radius:16px;padding:0.5em 1.2em;font-size:1.1em;'>Matches: <b>{num_matches}</b></span>" \
        f"<span style='background:#4CAF50;color:#fff;border-radius:16px;padding:0.5em 1.2em;font-size:1.1em;'>Avg. Score: <b>{avg_score:.1f}%</b></span>" \
        f"<span style='background:#F44336;color:#fff;border-radius:16px;padding:0.5em 1.2em;font-size:1.1em;'>Gaps: <b>{num_gaps}</b></span>" \
        "</div>", unsafe_allow_html=True)
    # Line chart: Top 3 matches by score
    if go:
        sorted_matrix = sorted(alignment_matrix, key=lambda x: x.get('match_score_percent', 0), reverse=True)
        top_matches = sorted_matrix[:3]
        if len(alignment_matrix) > 3:
            st.toast("Showing top 3 matches by score for readability. Refine your analysis for more detail.", icon="ℹ️")
        # Horizontal bar chart: Top 3 matches by score
        x_scores = [item.get('match_score_percent', 0) for item in top_matches]
        y_labels = ["" for _ in top_matches]  # No y-axis labels, only text inside bars
        hover_texts = [
            f"<b>Need:</b> {item.get('prospect_need') or item.get('customer_need', 'N/A')}<br>"
            f"<b>Component:</b> {item.get('our_value_component', 'N/A')}<br>"
            f"<b>Score:</b> {item.get('match_score_percent', 0)}%"
            for item in top_matches
        ]
        bar_texts = [(item.get('prospect_need') or item.get('customer_need', 'N/A')) for item in top_matches]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_scores,
            y=y_labels,
            orientation='h',
            text=bar_texts,
            textposition='inside',
            insidetextanchor='middle',
            marker=dict(color='#1976D2'),
            hoverinfo='text',
            hovertext=hover_texts
        ))
        fig.update_layout(
            title_text="Value Alignment Overview (Top 3 Matches)",
            xaxis_title="Match Score (%)",
            yaxis_title="",
            font_size=15,
            height=400,
            margin=dict(t=40, b=40, l=10, r=10),
            yaxis=dict(automargin=True)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Install plotly for a line chart overview.") 