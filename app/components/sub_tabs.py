import streamlit as st
import asyncio
from app.database import save_value_component, delete_value_component_by_key, fetch_all_value_components
from app.logic import analyze_technical_subcategory_components, calculate_and_save_value_bricks, generate_chain_of_thought
import logging
import json
from app.database import fetch_all_value_components
import hashlib
import uuid
from collections import Counter
from app.utils.spinner import multi_step_save_spinner
from app.components.universal_user_driven_validation import UniversalUserDrivenValidation
from app.config import DEBUG_MODE, DEBUG_WIDGET_KEYS, DEBUG_AI_PROCESSING, DEBUG_DATABASE_OPERATIONS

# Helper to run async functions in Streamlit
async def run_async(func, *args, **kwargs):
    return await func(*args, **kwargs)

# --- Ensure ai_regen_tasks is always initialized ---
if "ai_regen_tasks" not in st.session_state:
    st.session_state["ai_regen_tasks"] = {}

# --- Helper: Debounce AI regeneration ---
async def debounce_ai_regeneration(main_cat, sub_cat, comp_name, value, ai_processing_key, ai_processed_values, delay=0.5):
    if "ai_regen_tasks" not in st.session_state:
        st.session_state["ai_regen_tasks"] = {}
    task_key = f"regen_{main_cat}_{sub_cat}_{comp_name}"
    # Cancel any previous task
    prev_task = st.session_state["ai_regen_tasks"].get(task_key)
    if prev_task and not prev_task.done():
        prev_task.cancel()
    async def ai_regen_task():
        await asyncio.sleep(delay)
        # --- PATCH: If value is empty, skip AI and set processed value to empty ---
        if not value or not value.strip():
            ai_processed_values[main_cat][sub_cat][comp_name] = ""
            st.session_state[ai_processing_key] = False
            st.session_state["global_processing"] = False
            return
        st.session_state["global_processing"] = True
        st.session_state[ai_processing_key] = True
        try:
            if DEBUG_MODE or DEBUG_AI_PROCESSING:
                logging.info(f"[AI PROCESSING] Starting AI analysis for {comp_name} with value: {value[:100]}...")
            ai_result = await analyze_technical_subcategory_components(main_cat, {comp_name: value}, [comp_name])
            ai_benefit = ai_result.get(comp_name, {}).get("value_proposition", "") if ai_result else ""
            ai_processed_values[main_cat][sub_cat][comp_name] = ai_benefit
            if DEBUG_MODE or DEBUG_AI_PROCESSING:
                logging.info(f"[AI PROCESSING] Completed AI analysis for {comp_name}, result length: {len(ai_benefit)}")
        except Exception as e:
            ai_processed_values[main_cat][sub_cat][comp_name] = f"[AI error: {e}]"
            if DEBUG_MODE or DEBUG_AI_PROCESSING:
                logging.error(f"[AI PROCESSING] Error in AI analysis for {comp_name}: {e}")
        st.session_state[ai_processing_key] = False
        st.session_state["global_processing"] = False
    # Schedule new task
    st.session_state["ai_regen_tasks"][task_key] = asyncio.create_task(ai_regen_task())

async def render_sub_tabs(current_selected_main_category, component_structures, value_components, ai_processed_values, process_value_with_ai, calculate_and_save_value_bricks_func, refresh_callback=None):

    
    # --- Reset processing flags at the start of each render ---
    for sub_cat in component_structures[current_selected_main_category]["subcategories"]:
        ai_processing_key = f"ai_processing_{current_selected_main_category.lower()}_{sub_cat.lower()}"
        st.session_state[ai_processing_key] = False
    # Load previous state from value_components for comparison
    # Get user_id using demo profile manager for proper data isolation
    from app.components.demo_companies.demo_profile_manager import demo_profile_manager
    user_id = demo_profile_manager.get_current_user_id()
    all_db_components = fetch_all_value_components(user_id=user_id)
    # --- DEBUG: Print raw DB data ---
    if DEBUG_MODE or DEBUG_DATABASE_OPERATIONS:
        logging.warning(f"[sub_tabs.py][DEBUG] Raw all_db_components for user_id={user_id}: {all_db_components}")
    db_components = []
    if all_db_components is None:
        db_components = []
    elif isinstance(all_db_components, dict):
        db_components = all_db_components.get(current_selected_main_category.lower(), [])
    elif isinstance(all_db_components, list):
        # Type guard: ensure all_db_components is a list before iterating
        db_components = [c for c in all_db_components if c and (c.get("main_category") or "").lower() == current_selected_main_category.lower()]  # type: ignore[union-attr]
    # Build a lookup: (main_category, category, name) -> {original_value, ai_processed_value, chain_of_thought}, all lowercase
    db_lookup = {}
    for comp in db_components:
        key = (
            (comp.get("main_category") or "").lower(),
            (comp.get("category") or "").lower(),
            (comp.get("name") or "").lower()
        )
        db_lookup[key] = {
            "original_value": comp.get("original_value", ""),
            "ai_processed_value": comp.get("ai_processed_value", ""),
            "chain_of_thought": comp.get("chain_of_thought", ""),
            "user_rating": comp.get("user_rating", 1)
        }
    # --- DEBUG: Print built db_lookup keys ---
    if DEBUG_MODE or DEBUG_DATABASE_OPERATIONS:
        logging.warning(f"[sub_tabs.py][DEBUG] Built db_lookup keys: {list(db_lookup.keys())}")
    # --- Ensure ai_processed_values is always up to date with DB ---
    for comp in db_components:
        main_cat = comp.get("main_category")
        category = comp.get("category")
        name = comp.get("name")
        ai_val = comp.get("ai_processed_value", "")
        if main_cat and category and name:
            if main_cat not in ai_processed_values:
                ai_processed_values[main_cat] = {}
            if category not in ai_processed_values[main_cat]:
                ai_processed_values[main_cat][category] = {}
            ai_processed_values[main_cat][category][name] = ai_val
    # --- Ensure all subcategories and fields are present in session state, even if missing from DB ---
    # Also populate value_components from database at the start
    for sub_cat, subcat_details in component_structures[current_selected_main_category]["subcategories"].items():
        sub_cat_lc = sub_cat.lower()
        for comp in subcat_details["items"]:
            comp_name = comp["name"]
            comp_name_lc = comp_name.lower()
            # Initialize structure
            value_components.setdefault(current_selected_main_category.lower(), {}).setdefault(sub_cat_lc, {}).setdefault(comp_name_lc, "")
            ai_processed_values.setdefault(current_selected_main_category.lower(), {}).setdefault(sub_cat_lc, {}).setdefault(comp_name_lc, "")
            # Populate from database if data exists
            lookup_key = (
                (current_selected_main_category or "").lower(),
                (sub_cat or "").lower(),
                (comp_name or "").lower()
            )
            db_data = db_lookup.get(lookup_key, {})
            if db_data:
                # Populate original_value from database
                value_components[current_selected_main_category.lower()][sub_cat_lc][comp_name_lc] = db_data.get("original_value", "")
                # Populate ai_processed_value from database
                ai_processed_values[current_selected_main_category.lower()][sub_cat_lc][comp_name_lc] = db_data.get("ai_processed_value", "")
                # Also set rating if it exists
                rating = db_data.get("user_rating", 1)
                if rating:
                    value_components[current_selected_main_category.lower()][sub_cat_lc][comp_name_lc + "_rating"] = rating
    subcategories_details = component_structures[current_selected_main_category]["subcategories"]
    subcategory_labels = list(subcategories_details.keys())
    sub_tabs = st.tabs(subcategory_labels)
    widget_keys_this_render = set()
    key_bases_this_render = set()
    # Pre-render check for duplicate key_bases
    all_key_bases = []
    for j, subcategory in enumerate(subcategory_labels):
        for i, component_item in enumerate(subcategories_details[subcategory]["items"]):
            component_name = component_item["name"]
            # Use the same unique key base logic as in the widget generation
            unique_key_base = f"{current_selected_main_category}|{component_name.lower()}|{j}|{i}|{current_selected_main_category.lower()}"
            all_key_bases.append(unique_key_base.lower())  # Always lowercased
    key_base_counts = Counter(all_key_bases)
    duplicates = [k for k, v in key_base_counts.items() if v > 1]
    if duplicates:
        if DEBUG_MODE or DEBUG_WIDGET_KEYS:
            logging.error("[DUPLICATE KEY_BASE ERROR] The following key_bases are duplicated:")
            for dup in duplicates:
                logging.error(f"  {dup} (count={key_base_counts[dup]})")
            logging.error("ALL KEY_BASES THIS RENDER:")
            for idx, kb in enumerate(all_key_bases):
                logging.error(f"  [{idx}] {kb}")
        raise Exception(f"Duplicate widget key_base detected: {duplicates}. Please ensure each value component is unique per main category and subcategory.")
    # Diagnostic: Print duplicate component names in each subcategory
    for sub_cat, subcat_details in component_structures[current_selected_main_category]["subcategories"].items():
        names = [comp["name"] for comp in subcat_details["items"]]
        name_counts = Counter(names)
        dups = [n for n, c in name_counts.items() if c > 1]
        if dups:
            if DEBUG_MODE or DEBUG_WIDGET_KEYS:
                logging.error(f"[DUPLICATE COMPONENT NAME] In subcategory '{sub_cat}' of '{current_selected_main_category}': {dups}")
    for j, subcategory in enumerate(subcategory_labels):
        subcategory_lc = subcategory.lower()
        widget_namespace = f"{current_selected_main_category.lower()}_{subcategory_lc}"
        # Diagnostic: Print all component names and widget keys for Customer Support in After Sales Value
        if subcategory == "Customer Support" and current_selected_main_category == "After Sales Value":
            names = [comp["name"] for comp in subcategories_details[subcategory]["items"]]
            widget_keys = []
            for i, component_item in enumerate(subcategories_details[subcategory]["items"]):
                component_name = component_item["name"]
                key_base = f"{widget_namespace}|{component_name.lower()}|{j}|{i}"
                key_hash = hashlib.md5(key_base.encode()).hexdigest()[:8]
                input_key = f"{widget_namespace}_input_{key_hash}".lower()
                widget_keys.append(input_key)
            if DEBUG_MODE or DEBUG_WIDGET_KEYS:
                logging.error(f"[RENDER COMPONENTS] {current_selected_main_category} | {subcategory} | names: {names} | widget_keys: {widget_keys}")
        with sub_tabs[j]:
            with st.container():
                st.markdown(f"#### {subcategory}")
                ai_processing_key = f"ai_processing_{current_selected_main_category.lower()}_{subcategory_lc}"
                if ai_processing_key not in st.session_state:
                    st.session_state[ai_processing_key] = False
                if "global_processing" not in st.session_state:
                    st.session_state["global_processing"] = False
                
                # Create a container for expandables with 50% width
                expander_container = st.container()
                with expander_container:
                    # Use columns to make expandables 50% width
                    col1, col2, col3 = st.columns([1, 0.2, 1])
                    
                    # Left column: All expanders stacked vertically
                    with col1:
                        for i, component_item in enumerate(subcategories_details[subcategory]["items"]):
                            # ENFORCE LOWERCASE CONSISTENCY FOR ALL KEYS
                            component_name = component_item["name"]
                            component_name_lc = component_name.lower()
                            component_description = component_item["description"]
                            component_tooltip = component_item.get("tooltip", None)
                            current_value = value_components[current_selected_main_category.lower()][subcategory_lc].get(component_name_lc, "")
                            # Debug logging to see what value is being used
                            if DEBUG_MODE or DEBUG_WIDGET_KEYS:
                                logging.info(f"[WIDGET VALUE] {component_name_lc}: current_value='{current_value}' from value_components[{current_selected_main_category.lower()}][{subcategory_lc}][{component_name_lc}]")
                            # Create a more unique key base to prevent collisions
                            # Use a combination of namespace, component name, position, and main category
                            unique_key_base = f"{widget_namespace}|{component_name_lc}|{j}|{i}|{current_selected_main_category.lower()}"
                            key_hash = hashlib.md5(unique_key_base.encode()).hexdigest()[:8]
                            input_key = f"{widget_namespace}_input_{key_hash}".lower()
                            ai_key = f"{widget_namespace}_ai_processed_{key_hash}".lower()
                            rating_key = f"{widget_namespace}_rating_{key_hash}".lower()
                            clear_key = f"{widget_namespace}_clear_{key_hash}".lower()
                            cot_key = f"{widget_namespace}_{component_name_lc}_chain_of_thought_{key_hash}".lower()
                            # Get clear_checked value from session state (default to False)
                            # If there's no data in the database, don't show as cleared
                            db_key = (current_selected_main_category.lower(), subcategory_lc, component_name_lc)
                            has_db_data = db_key in db_lookup
                            
                            # If no data in database, force clear checkbox to False
                            if not has_db_data:
                                if clear_key in st.session_state:
                                    st.session_state[clear_key] = False
                                clear_checked = False
                            else:
                                clear_checked = st.session_state.get(clear_key, False)
                            # Get chain-of-thought from database lookup
                            db_cot = db_lookup.get((current_selected_main_category.lower(), subcategory_lc, component_name_lc), {}).get("chain_of_thought", "")
                            cot_val = db_cot
                            # Track widget keys for this render
                            for k in [input_key, ai_key, rating_key, clear_key, cot_key]:
                                widget_keys_this_render.add(k)
                            # Debug widget keys only if enabled
                            if DEBUG_MODE or DEBUG_WIDGET_KEYS:
                                print(f"[DEBUG] Widget keys: input={input_key}, ai={ai_key}, rating={rating_key}, clear={clear_key}, cot={cot_key}")
                                logging.debug(f"[WIDGET RENDER] key_base={unique_key_base}, key_hash={key_hash}, input_key={input_key}")
                            widget_keys_this_render.add(input_key)
                            # Create expander title with component name (bold) and description (in parentheses, not bold)
                            expander_title = f"**{component_name}** ({component_description})"
                            
                            # Define slider_key and star_labels before if/else block so they're available in both branches
                            slider_key = f"slider_{widget_namespace}_{component_name_lc}_{key_hash}"
                            star_labels = {0: "(cleared)", 1: "★☆☆", 2: "★★☆", 3: "★★★"}
                            
                            # Create a container with expander and help icon side by side
                            if component_tooltip:
                                col1, col2 = st.columns([1, 0.05])
                                with col1:
                                    with st.expander(expander_title, expanded=False):
                                        st.markdown(f"**User Input:**")
                                        # Use universal validation interface
                                        validation_interface = UniversalUserDrivenValidation()
                                        # Show empty value if clear is checked or no data in database
                                        display_value = "" if clear_checked or not has_db_data else current_value
                                        new_value = await validation_interface.create_validation_interface(
                                            component_name,
                                            component_description,
                                            current_selected_main_category,
                                            subcategory,
                                            display_value,
                                            component_tooltip
                                        )
                                        value_components[current_selected_main_category.lower()][subcategory_lc][component_name_lc] = new_value
                                        st.markdown("**Customer Benefit:**")
                                        ai_value = ai_processed_values[current_selected_main_category.lower()][subcategory_lc].get(component_name_lc, "")
                                        # Show empty if clear is checked or no data in database
                                        display_ai_value = "" if clear_checked or not has_db_data else ai_value
                                        st.info(display_ai_value or "Enter text and click Save to see AI-processed customer benefits")
                                        
                                        clear_checkbox = st.checkbox("Clear", key=clear_key)
                                        if clear_checkbox:
                                            # Clear everything when checkbox is checked
                                            ai_processed_values[current_selected_main_category.lower()][subcategory_lc][component_name_lc] = ""
                                            value_components[current_selected_main_category.lower()][subcategory_lc][component_name_lc] = ""
                                            st.rerun()
                                        
                                        # Importance rating slider
                                        # Get the current rating from DB or default to 1, but use 0 if clear is checked or no data
                                        current_rating = db_lookup.get((current_selected_main_category.lower(), subcategory_lc, component_name_lc), {"user_rating": 1}).get("user_rating", 1)
                                        if clear_checked or not has_db_data:
                                            current_rating = 0  # Force to 0 when cleared or no data
                                        slider_value = st.slider(
                                            "Importance (stars)",
                                            min_value=0,
                                            max_value=3,
                                            value=current_rating,
                                            format="%d",
                                            key=slider_key,
                                            help="Rate the importance of this field (0=cleared, 1=low, 3=high)"
                                        )
                                        if clear_checked or not has_db_data:
                                            st.write("(cleared)")
                                        else:
                                            st.write(star_labels.get(slider_value, ""))
                                        # Update value_components with slider value
                                        value_components[current_selected_main_category.lower()][subcategory_lc][component_name_lc + "_rating"] = slider_value
                                        
                                        # Chain-of-Thought Reasoning expander (positioned after importance stars)
                                        with st.expander("Chain-of-Thought Reasoning", expanded=False):
                                            st.success(cot_val or "No chain-of-thought reasoning generated yet.")
                                with col2:
                                    # Add help icon aligned with expander title
                                    escaped_tooltip = component_tooltip.replace('"', '&quot;')
                                    st.markdown(f"""
                                    <style>
                                    .help-tooltip {{
                                        position: relative;
                                        display: inline-block;
                                    }}
                                    .help-tooltip .tooltiptext {{
                                        visibility: hidden;
                                        width: 300px;
                                        background-color: #fff3cd;
                                        color: #856404;
                                        text-align: left;
                                        border-radius: 6px;
                                        padding: 8px 12px;
                                        position: absolute;
                                        z-index: 1;
                                        bottom: 125%;
                                        left: 50%;
                                        margin-left: -150px;
                                        opacity: 0;
                                        transition: opacity 0.3s;
                                        border: 1px solid #ffeaa7;
                                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                                        font-size: 12px;
                                        line-height: 1.4;
                                    }}
                                    .help-tooltip:hover .tooltiptext {{
                                        visibility: visible;
                                        opacity: 1;
                                    }}
                                    </style>
                                    <div style='margin-top: 8px;'>
                                        <div class="help-tooltip">
                                            <span style='background-color: #ff8c00; color: white; border-radius: 50%; width: 16px; height: 16px; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; cursor: help; vertical-align: middle; box-shadow: 0 2px 4px rgba(0,0,0,0.2);' onmouseover='this.style.backgroundColor="#ff6b00"' onmouseout='this.style.backgroundColor="#ff8c00"'>?</span>
                                            <span class="tooltiptext">{escaped_tooltip}</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                with st.expander(expander_title, expanded=False):
                                    st.markdown(f"**User Input:**")
                                    # Use universal validation interface
                                    validation_interface = UniversalUserDrivenValidation()
                                    # Show empty value if clear is checked or no data in database
                                    display_value = "" if clear_checked or not has_db_data else current_value
                                    new_value = await validation_interface.create_validation_interface(
                                        component_name,
                                        component_description,
                                        current_selected_main_category,
                                        subcategory,
                                        display_value,
                                        component_tooltip
                                    )
                                    value_components[current_selected_main_category.lower()][subcategory_lc][component_name_lc] = new_value
                                    st.markdown("**Customer Benefit:**")
                                    ai_value = ai_processed_values[current_selected_main_category.lower()][subcategory_lc].get(component_name_lc, "")
                                    # Show empty if clear is checked or no data in database
                                    display_ai_value = "" if clear_checked or not has_db_data else ai_value
                                st.info(display_ai_value or "Enter text and click Save to see AI-processed customer benefits")
                                
                                clear_checkbox = st.checkbox("Clear", key=clear_key)
                                if clear_checkbox:
                                    # Clear everything when checkbox is checked
                                    ai_processed_values[current_selected_main_category.lower()][subcategory_lc][component_name_lc] = ""
                                    value_components[current_selected_main_category.lower()][subcategory_lc][component_name_lc] = ""
                                    # Set rating to 0 (cleared)
                                    value_components[current_selected_main_category.lower()][subcategory_lc][component_name_lc + "_rating"] = 0
                                    # Note: Don't modify session state here - it will be handled in the save function
                                clear_checked = st.session_state[clear_key]
                                # Move the slider (stars) inside the expander
                                # Get the current rating from DB or default to 1, but use 0 if clear is checked or no data
                                current_rating = db_lookup.get((current_selected_main_category.lower(), subcategory_lc, component_name_lc), {"user_rating": 1}).get("user_rating", 1)
                                if clear_checked or not has_db_data:
                                    current_rating = 0  # Force to 0 when cleared or no data
                                slider_value = st.slider(
                                    "Importance (stars)",
                                    min_value=0,
                                    max_value=3,
                                    value=current_rating,
                                    format="%d",
                                    key=slider_key,
                                    help="Rate the importance of this field (0=cleared, 1=low, 3=high)"
                                )
                                if clear_checked or not has_db_data:
                                    st.write("(cleared)")
                                else:
                                    st.write(star_labels.get(slider_value, ""))
                                # Update value_components with slider value
                                value_components[current_selected_main_category.lower()][subcategory_lc][component_name_lc + "_rating"] = slider_value
                                
                                # Chain-of-Thought Reasoning expander (positioned after importance stars)
                                with st.expander("Chain-of-Thought Reasoning", expanded=False):
                                    st.success(cot_val or "No chain-of-thought reasoning generated yet.")
                    

                    
                    # Middle column: Spacing and visual separation
                    with col2:
                        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
                    
                    # Right column: Summary and save button
                    with col3:
                        # Calculate component data
                        component_count = len(subcategories_details[subcategory]["items"])
                        
                        # Count fields with generated customer benefits
                        fields_with_benefits = 0
                        for comp in subcategories_details[subcategory]["items"]:
                            comp_name = comp["name"]
                            comp_name_lc = comp_name.lower()
                            # Check if this component has AI-generated content in the database
                            db_key = (current_selected_main_category.lower(), subcategory_lc, comp_name_lc)
                            db_ai_val = db_lookup.get(db_key, {"ai_processed_value": ""}).get("ai_processed_value", "")
                            if db_ai_val and db_ai_val.strip():
                                fields_with_benefits += 1
                        
                        # [NEW] Simple summary with soft motivation (replaces original summary)
                        try:
                            # Import simple summary panel
                            from app.components.simple_summary_panel import simple_summary_panel
                            
                            # Render simple summary with soft motivation
                            simple_summary_panel.render_simple_summary(
                                current_selected_main_category, 
                                subcategory, 
                                component_count, 
                                fields_with_benefits, 
                                db_lookup, 
                                subcategories_details
                            )
                            
                        except Exception as e:
                            st.error(f"Unable to load quality assessment: {e}")
                            # Fallback to basic summary if quality assessment fails
                            st.markdown(f"### {subcategory}")
                            st.markdown(f"**{component_count} components** • Focus on {subcategory.lower()} standards and practices")
                            
                            if fields_with_benefits == 0:
                                st.info(f"**0 fields with generated customer benefits**\n\nStart by entering text in the left column and clicking Save to generate AI insights.")
                            elif fields_with_benefits == component_count:
                                st.success(f"**{fields_with_benefits}/{component_count} fields completed!** 🎉\n\nAll components have AI-generated customer benefits.")
                            else:
                                st.warning(f"**{fields_with_benefits}/{component_count} fields completed**\n\n{component_count - fields_with_benefits} more components need customer benefits.")
                            
                            st.markdown("<br><br>", unsafe_allow_html=True)
                
                # Add spacing between expandables and save button
                st.markdown("<br><br>", unsafe_allow_html=True)
                
                # Improved save button with better styling
                save_key = f"save_{current_selected_main_category}_{subcategory}"
                if DEBUG_MODE or DEBUG_WIDGET_KEYS:
                    logging.error(f"[SAVE BUTTON] save_key={save_key} for subcategory={subcategory} and main_category={current_selected_main_category}")
                # --- Disable Save button if AI is processing ---
                save_disabled = st.session_state.get(ai_processing_key, False) or st.session_state.get("global_processing", False)
                
                # Show processing status if button is disabled
                if save_disabled:
                    st.info("🔄 Processing in progress... Please wait for the current operation to complete.")
                
                # Create a container for the button
                button_container = st.container()
                with button_container:
                    # Additional check to prevent rendering if already processing
                    is_currently_processing = st.session_state.get("global_processing", False) or st.session_state.get(ai_processing_key, False)
                    
                    if st.button(f"💾 Save {subcategory} Components for {current_selected_main_category}", 
                               key=save_key, 
                               disabled=save_disabled or is_currently_processing,
                               help="Click to save all changes for this subcategory" if not is_currently_processing else "Processing in progress",
                               type="primary"):
                        
                        # Additional safety check - if already processing, don't proceed
                        if st.session_state.get("global_processing", False) or st.session_state.get(ai_processing_key, False):
                            st.warning("⚠️ Operation already in progress. Please wait.")
                            return
                        
                        # CRITICAL: Set processing flags IMMEDIATELY to prevent double-clicks
                        st.session_state["global_processing"] = True
                        st.session_state[ai_processing_key] = True
                        
                        # Define the steps for multi-step spinner
                        steps = [
                            {
                                "name": "analyze",
                                "message": "Analyzing changes and preparing data"
                            },
                            {
                                "name": "clear",
                                "count": 0,  # Will be updated below
                                "message": "Clearing fields from database"
                            },
                            {
                                "name": "ai_processing",
                                "count": 0,  # Will be updated below
                                "message": "Generating AI insights"
                            },
                            {
                                "name": "save",
                                "count": 0,  # Will be updated below
                                "message": "Saving AI-processed components"
                            },
                            {
                                "name": "rating",
                                "count": 0,  # Will be updated below
                                "message": "Updating ratings"
                            },
                            {
                                "name": "refresh",
                                "message": "Refreshing UI with latest data"
                            }
                        ]
                        
                        # Analyze changes first to get counts
                        fields_to_clear = []
                        fields_to_update_with_ai = []
                        fields_to_update_rating_only = []
                        ai_input = {}
                        rerun_needed = False
                        cleared_any = False
                        
                        for comp in subcategories_details[subcategory]["items"]:
                            comp_name = comp["name"]
                            comp_name_lc = comp_name.lower()
                            input_key = f"input_{current_selected_main_category}_{subcategory}_{comp_name}"
                            ai_key = f"ai_processed_{current_selected_main_category}_{subcategory}_{comp_name}"
                            rating_key = f"rating_{current_selected_main_category}_{subcategory}_{comp_name}"
                            # Use the same key generation as in widget creation for clear checkbox
                            widget_namespace = f"{current_selected_main_category.lower()}_{subcategory.lower()}"
                            # Find the correct indices for this component
                            comp_index = None
                            for idx, comp_item in enumerate(subcategories_details[subcategory]["items"]):
                                if comp_item["name"] == comp_name:
                                    comp_index = idx
                                    break
                            
                            if comp_index is not None:
                                unique_key_base = f"{widget_namespace}|{comp_name_lc}|{j}|{comp_index}|{current_selected_main_category.lower()}"
                                key_hash = hashlib.md5(unique_key_base.encode()).hexdigest()[:8]
                                clear_key = f"{widget_namespace}_clear_{key_hash}".lower()
                                clear_checked = st.session_state.get(clear_key, False)
                            else:
                                clear_checked = False
                            user_val = value_components[current_selected_main_category.lower()][subcategory.lower()].get(comp_name_lc, "")
                            db_key = (current_selected_main_category.lower(), subcategory.lower(), comp_name_lc)
                            db_val = db_lookup.get(db_key, {"original_value": ""}).get("original_value", "")
                            db_ai_val = db_lookup.get(db_key, {"ai_processed_value": ""}).get("ai_processed_value", "")
                            db_rating = db_lookup.get(db_key, {"user_rating": 1}).get("user_rating", 1)
                            # Use the stateless slider value from value_components for saving
                            rating_val = value_components[current_selected_main_category.lower()][subcategory.lower()].get(comp_name_lc + "_rating", 1)
                            # Also get the slider value from session state as backup
                            # Use the same key generation as in widget creation
                            widget_namespace = f"{current_selected_main_category.lower()}_{subcategory.lower()}"
                            # Find the correct indices for this component
                            comp_index = None
                            for idx, comp_item in enumerate(subcategories_details[subcategory]["items"]):
                                if comp_item["name"] == comp_name:
                                    comp_index = idx
                                    break
                            if comp_index is not None:
                                unique_key_base = f"{widget_namespace}|{comp_name_lc}|{j}|{comp_index}|{current_selected_main_category.lower()}"
                                key_hash = hashlib.md5(unique_key_base.encode()).hexdigest()[:8]
                                slider_key = f"slider_{widget_namespace}_{comp_name_lc}_{key_hash}"
                                if slider_key in st.session_state:
                                    rating_val = st.session_state[slider_key]
                            # 1. Clear checked: delete from DB, clear session/local state
                            if clear_checked:
                                fields_to_clear.append({
                                    "main_category": current_selected_main_category,
                                    "category": subcategory,
                                    "name": comp_name
                                })
                                # Clear all local cache values
                                ai_processed_values[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc] = ""
                                value_components[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc] = ""
                                # Reset rating to 0 (cleared)
                                value_components[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc + "_rating"] = 0
                                rerun_needed = True
                                cleared_any = True
                                continue
                            # 2. User input changed (not cleared): update with AI and save
                            if user_val.strip() and (user_val.strip() != db_val.strip() or db_val == ""):
                                fields_to_update_with_ai.append({
                                    "main_category": current_selected_main_category,
                                    "category": subcategory,
                                    "name": comp_name,
                                    "original_value": user_val,
                                    "user_rating": rating_val
                                })
                                ai_input[comp_name] = user_val
                                # Don't modify session state after widget instantiation
                                continue
                            # 3. Only rating changed: update rating only
                            if (user_val.strip() == db_val.strip()) and (rating_val != db_rating):
                                fields_to_update_rating_only.append({
                                    "main_category": current_selected_main_category,
                                    "category": subcategory,
                                    "name": comp_name,
                                    "original_value": user_val,
                                    "user_rating": rating_val,
                                    "ai_processed_value": db_ai_val
                                })
                                # Don't modify session state after widget instantiation
                                continue
                            # 4. No change: do nothing
                        
                        # Update step counts
                        steps[1]["count"] = len(fields_to_clear)
                        steps[2]["count"] = len(fields_to_update_with_ai)
                        steps[3]["count"] = len(fields_to_update_with_ai)
                        steps[4]["count"] = len(fields_to_update_rating_only)
                        
                        # Processing flags already set above to prevent double-clicks
                        
                        try:
                            with multi_step_save_spinner(steps):
                                # Step 1: Analyze changes (already done above)
                                
                                # Step 2: Clear fields from database
                                for field in fields_to_clear:
                                    if DEBUG_MODE or DEBUG_DATABASE_OPERATIONS:
                                        logging.warning(f"[sub_tabs.py][DEBUG] Deleting field from DB: {field}")
                                    delete_value_component_by_key(field["main_category"], field["category"], field["name"], user_id=user_id)
                                    # Also clear any rating data for this component
                                    rating_key = f"{field['name'].lower()}_rating"
                                    if rating_key in value_components[field["main_category"].lower()][field["category"].lower()]:
                                        value_components[field["main_category"].lower()][field["category"].lower()][rating_key] = 0
                                    
                                                                         # Note: Clear checkbox state will be reset in the next render cycle
                                     # after the field is removed from the database
                                
                                # Step 3: Process AI updates
                                ai_results = {}
                                if fields_to_update_with_ai:
                                    if DEBUG_MODE or DEBUG_AI_PROCESSING:
                                        logging.warning(f"[sub_tabs.py][DEBUG] Sending to AI: {ai_input}")
                                    ai_results = await analyze_technical_subcategory_components(current_selected_main_category, ai_input, list(ai_input.keys()))
                                    if DEBUG_MODE or DEBUG_AI_PROCESSING:
                                        logging.warning(f"[sub_tabs.py][DEBUG] AI results: {ai_results}")
                                
                                # Step 4: Save AI-processed components
                                if fields_to_update_with_ai:
                                    for field in fields_to_update_with_ai:
                                        comp_name = field["name"]
                                        ai_benefit = ai_results.get(comp_name, {}).get("value_proposition", "") if ai_results else ""
                                        percent = ai_results.get(comp_name, {}).get("percentage", 0.0) if ai_results else 0.0
                                        
                                        # Generate chain-of-thought reasoning
                                        chain_of_thought = ""
                                        if ai_benefit and field["original_value"]:
                                            try:
                                                from app.core.company_context_manager import CompanyContextManager
                                                company_context = CompanyContextManager()
                                                company_background = company_context.get_core_business()
                                                chain_of_thought = await generate_chain_of_thought(
                                                    company_background, 
                                                    field["original_value"], 
                                                    ai_benefit, 
                                                    comp_name
                                                )
                                            except Exception as e:
                                                if DEBUG_MODE or DEBUG_AI_PROCESSING:
                                                    logging.warning(f"[sub_tabs.py][DEBUG] Failed to generate chain-of-thought for {comp_name}: {e}")
                                                chain_of_thought = "Chain-of-thought reasoning could not be generated."
                                        
                                        # Get current user_id from demo_profile_manager (handles demo/normal mode correctly)
                                        user_id = demo_profile_manager.get_current_user_id()
                                        payload = {
                                            "main_category": field["main_category"],
                                            "category": field["category"],
                                            "name": comp_name,
                                            "original_value": field["original_value"],
                                            "ai_processed_value": ai_benefit,
                                            "chain_of_thought": chain_of_thought,
                                            "weight": percent,
                                            "user_rating": field["user_rating"],
                                            "user_id": user_id  # Explicit user_id for data isolation
                                        }
                                        if DEBUG_MODE or DEBUG_DATABASE_OPERATIONS:
                                            logging.warning(f"[sub_tabs.py][DEBUG] Saving with AI: {payload}")
                                        save_value_component(payload)
                                
                                # Step 5: Save rating-only updates
                                if fields_to_update_rating_only:
                                    # Get current user_id from demo_profile_manager (handles demo/normal mode correctly)
                                    user_id = demo_profile_manager.get_current_user_id()
                                    for field in fields_to_update_rating_only:
                                        payload = {
                                            "main_category": field["main_category"],
                                            "category": field["category"],
                                            "name": field["name"],
                                            "original_value": field["original_value"],
                                            "ai_processed_value": field["ai_processed_value"],
                                            "weight": 0,  # Optionally recalculate if needed
                                            "user_rating": field["user_rating"],
                                            "user_id": user_id  # Explicit user_id for data isolation
                                        }
                                        if DEBUG_MODE or DEBUG_DATABASE_OPERATIONS:
                                            logging.warning(f"[sub_tabs.py][DEBUG] Saving rating only: {payload}")
                                        save_value_component(payload)
                                
                                # Step 6: Refresh UI data
                                st.cache_data.clear()
                                # FIX: Get user_id using demo profile manager for proper data isolation
                                user_id = demo_profile_manager.get_current_user_id()
                                all_db_components = fetch_all_value_components(user_id=user_id)
                                db_components = []
                                if all_db_components is None:
                                    db_components = []
                                elif isinstance(all_db_components, dict):
                                    db_components = all_db_components.get(current_selected_main_category, [])
                                elif isinstance(all_db_components, list):
                                    # Type guard: ensure all_db_components is a list before iterating
                                    db_components = [c for c in all_db_components if c and c.get("main_category") == current_selected_main_category]  # type: ignore[union-attr]
                                db_lookup = {}
                                for comp in db_components:
                                    key = (
                                        (comp.get("main_category") or "").lower(),
                                        (comp.get("category") or "").lower(),
                                        (comp.get("name") or "").lower()
                                    )
                                    db_lookup[key] = {
                                        "original_value": comp.get("original_value", ""),
                                        "ai_processed_value": comp.get("ai_processed_value", ""),
                                        "chain_of_thought": comp.get("chain_of_thought", ""),
                                        "user_rating": comp.get("user_rating", 1)
                                    }
                                # Update value_components and ai_processed_values from DB instead of st.session_state for input widgets
                                for comp in subcategories_details[subcategory]["items"]:
                                    comp_name = comp["name"]
                                    comp_name_lc = comp_name.lower()
                                    input_key = f"input_{current_selected_main_category}_{subcategory}_{comp_name}"
                                    ai_key = f"ai_processed_{current_selected_main_category}_{subcategory}_{comp_name}"
                                    rating_key = f"rating_{current_selected_main_category}_{subcategory}_{comp_name}"
                                    lookup_key = (
                                        (current_selected_main_category or "").lower(),
                                        (subcategory or "").lower(),
                                        (comp_name or "").lower()
                                    )
                                    db_value = db_lookup.get(lookup_key, {"original_value": ""}).get("original_value", "")
                                    ai_db_value = db_lookup.get(lookup_key, {"ai_processed_value": ""}).get("ai_processed_value", "")
                                    db_cot_value = db_lookup.get(lookup_key, {"chain_of_thought": ""}).get("chain_of_thought", "")
                                    db_rating = db_lookup.get(lookup_key, {"user_rating": 1}).get("user_rating", 1)
                                    # Update value_components and ai_processed_values from DB
                                    value_components[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc] = db_value
                                    ai_processed_values[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc] = ai_db_value
                                    st.session_state[ai_key] = ai_db_value
                            
                            # Clear processing flags
                            st.session_state["global_processing"] = False
                            st.session_state[ai_processing_key] = False
                            
                            # Show success message with summary
                            total_operations = len(fields_to_clear) + len(fields_to_update_with_ai) + len(fields_to_update_rating_only)
                            if total_operations > 0:
                                operations_summary = []
                                if fields_to_clear:
                                    operations_summary.append(f"{len(fields_to_clear)} cleared")
                                if fields_to_update_with_ai:
                                    operations_summary.append(f"{len(fields_to_update_with_ai)} AI-processed")
                                if fields_to_update_rating_only:
                                    operations_summary.append(f"{len(fields_to_update_rating_only)} ratings updated")
                                
                                summary_text = ", ".join(operations_summary)
                                st.toast(f"Successfully saved {subcategory} components: {summary_text}", icon="✅")
                            else:
                                st.toast("No changes detected - nothing to save", icon="ℹ️")
                            
                            # Force refresh by updating the value_components dictionary
                            # and ensuring the widgets will use the updated values
                            for comp in subcategories_details[subcategory]["items"]:
                                comp_name = comp["name"]
                                comp_name_lc = comp_name.lower()
                                lookup_key = (
                                    (current_selected_main_category or "").lower(),
                                    (subcategory or "").lower(),
                                    (comp_name or "").lower()
                                )
                                db_value = db_lookup.get(lookup_key, {"original_value": ""}).get("original_value", "")
                                db_rating = db_lookup.get(lookup_key, {"user_rating": 1}).get("user_rating", 1)
                                
                                # Update the value_components dictionary with the database value
                                value_components[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc] = db_value
                                
                                # Update rating - if field was cleared, set rating to 0
                                if comp_name_lc in [f["name"].lower() for f in fields_to_clear]:
                                    value_components[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc + "_rating"] = 0
                                else:
                                    value_components[current_selected_main_category.lower()][subcategory.lower()][comp_name_lc + "_rating"] = db_rating
                                
                                # Also update the session state for the AI processed value
                                ai_db_value = db_lookup.get(lookup_key, {"ai_processed_value": ""}).get("ai_processed_value", "")
                                ai_key = f"ai_processed_{current_selected_main_category}_{subcategory}_{comp_name}"
                                st.session_state[ai_key] = ai_db_value
                                
                                # Log the update for debugging
                                logging.info(f"Updated value_components[{current_selected_main_category.lower()}][{subcategory.lower()}][{comp_name_lc}] = '{db_value}' (rating: {db_rating})")
                            
                                                         # Reset all clear checkboxes after successful save
                             # Note: We'll handle this in the next render cycle after rerun
                             # The clear checkboxes will be reset because the fields are no longer in the database
                            
                            # Force a complete rerun to refresh all widgets
                            st.cache_data.clear()
                            
                            st.rerun()
                            
                        except Exception as e:
                            # Ensure spinners are cleared on error
                            st.session_state["global_processing"] = False
                            st.session_state[ai_processing_key] = False
                            
                            # Log the error
                            logging.error(f"[sub_tabs.py][ERROR] Error during save operation: {str(e)}", exc_info=True)
                            
                            # Show error message to user
                            st.error(f"❌ Error during save operation: {str(e)}")
                            st.toast(f"❌ Save failed: {str(e)}", icon="❌")
                            
                            # Don't rerun on error to allow user to see the error message 