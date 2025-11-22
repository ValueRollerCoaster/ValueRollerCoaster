import streamlit as st
from typing import Optional
from app.components.value_alignment.summary_bar import render_summary_bar
from app.components.value_alignment.top_matches import render_top_matches
from app.components.value_alignment.opportunities import render_opportunities
from app.components.value_alignment.matrix_heatmap import render_matrix_heatmap
from app.components.value_alignment.details_modal import render_details_modal

def display_value_alignment_tab(playbook_data: dict):
    # 1. Summary bar at the top
    render_summary_bar(playbook_data)
    # 2. (Category tabs removed)
    # 3. Top matches for all data
    selected_alignment = render_top_matches(playbook_data)
    # 4. Opportunities (unmatched needs)
    render_opportunities(playbook_data, None)  # type: ignore[arg-type]
    # 5. Optional: Expandable matrix/heatmap for advanced users
    render_matrix_heatmap(playbook_data, None)  # type: ignore[arg-type]
    # 6. Details modal/drawer for selected alignment
    if selected_alignment:
        render_details_modal(selected_alignment) 