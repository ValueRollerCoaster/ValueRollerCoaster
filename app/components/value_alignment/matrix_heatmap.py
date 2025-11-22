import streamlit as st
import pandas as pd
from typing import Optional
try:
    import plotly.express as px
except ImportError:
    px = None

def render_matrix_heatmap(playbook_data: dict, selected_category: Optional[str]):
    alignment_matrix = playbook_data.get("alignment_matrix") or []
    with st.expander("Show Full Value Alignment Matrix (Advanced)", expanded=False):
        if not alignment_matrix:
            st.info("No value alignment data available.")
            return
        # Prepare data
        needs = []
        components = set()
        data = []
        for item in alignment_matrix:
            need = item.get("prospect_need") or item.get("customer_need", "N/A")
            value_component = item.get("our_value_component") or item.get("our_component", "N/A")
            match_score = item.get("match_score_percent")
            # Only apply category filter if selected_category is set and not 'All'
            if selected_category and selected_category != "All":
                if not value_component.lower().startswith(selected_category.lower()):
                    continue
            needs.append(need)
            components.add(value_component)
            data.append((need, value_component, match_score))
        needs = list(dict.fromkeys(needs))
        components = list(components)
        # Create DataFrame with proper index and columns
        df = pd.DataFrame(0, index=pd.Index(needs), columns=pd.Index(components))
        for need, comp, score in data:
            df.at[need, comp] = score if score is not None else 0
        if px:
            fig = px.imshow(
                df,
                labels=dict(x="Value Component", y="Customer Need", color="Match Score (%)"),
                x=components,
                y=needs,
                color_continuous_scale="Blues",
                aspect="auto",
                text_auto=True
            )
            fig.update_layout(height=min(600, 40*len(needs)+120), margin=dict(t=40, b=40, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            st.info("Install plotly for a more interactive heatmap visualization.") 