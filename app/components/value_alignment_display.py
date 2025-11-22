import streamlit as st
from statistics import mean
import pandas as pd
# Try to import plotly, fallback to None if not available
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    px = None
    go = None

# Add some emoji icons for visual cues
NEED_ICON = "🎯"
COMPONENT_ICON = "💎"
MATCH_ICON = "✅"
UNMATCHED_ICON = "🟡"

CARD_STYLE = """
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 8px #0001;
    padding: 1.2em 1.5em 1.2em 1.5em;
    margin-bottom: 1.2em;
    border: 1.5px solid #e3e8f0;
"""

BADGE_STYLE = """
    display: inline-block;
    background: #e3e8f0;
    color: #333;
    border-radius: 16px;
    padding: 0.2em 0.9em;
    font-size: 1em;
    margin: 0.2em 0.3em 0.2em 0;
"""

CATEGORY_OPTIONS = [
    "All",
    "Technical Value",
    "Business Value",
    "Strategic Value",
    "After Sales Value"
]

CONTAINER_STYLE = """
    max-width: 1100px;
    margin-left: auto;
    margin-right: auto;
    padding: 1.5em 0 2em 0;
"""

from app.components.value_alignment.main_display import display_value_alignment_tab

def display_advanced_value_alignment(playbook_data: dict):
    display_value_alignment_tab(playbook_data) 