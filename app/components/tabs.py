from app.components.value_components.value_components_tab import render_value_components_tab

import streamlit as st
from typing import Dict, Callable, List, Any
from app.categories import COMPONENT_STRUCTURES
import math
import inspect
import sys
import logging
from app.database import fetch_all_value_components, save_value_component, get_value_components
from app.components.sub_tabs import render_sub_tabs

def excepthook(type, value, traceback):
    print("UNCAUGHT EXCEPTION:", value)
sys.excepthook = excepthook

# Refactor: Move main tab logic to value_components_tab.py and sub-tab/component logic to sub_tabs.py
# Remove the inlined render_main_and_sub_tabs and related logic from this file.

# Remove the inlined render_main_and_sub_tabs and related logic from this file. 