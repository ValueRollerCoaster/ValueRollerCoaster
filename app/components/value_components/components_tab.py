from app.categories import COMPONENT_STRUCTURES
from app.components.sub_tabs import render_sub_tabs

async def render_components_tab(selected_main_category, value_components, ai_processed_values, process_value_with_ai, calculate_and_save_value_bricks, refresh_callback):
    await render_sub_tabs(selected_main_category, COMPONENT_STRUCTURES, value_components, ai_processed_values, process_value_with_ai, calculate_and_save_value_bricks, refresh_callback) 