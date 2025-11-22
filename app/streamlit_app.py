import sys
import asyncio
import streamlit as st
import logging
import os

# --- Initialize Robustness System ---
from app.utils.robustness_integration import initialize_robustness_system, get_system_status, check_and_reset_stuck_operations

# Initialize robustness system
initialize_robustness_system()

# --- App-wide spinner overlay with robustness ---
if st.session_state.get('global_processing', False):
    # Check for stuck operations
    check_and_reset_stuck_operations()
    
    # Get system status
    system_status = get_system_status()
    
    # Show enhanced processing overlay
    st.markdown(
        '''
        <div style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;
                    background:rgba(255,255,255,0.7);display:flex;align-items:center;justify-content:center;">
            <div>
                <img src="https://i.gifer.com/ZZ5H.gif" width="80"/>
                <p style="font-size:1.5em;">Processing, please wait...</p>
                <p style="font-size:0.8em;color:#666;">System is working on your request</p>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
    
    # Show system status in sidebar for debugging
    with st.sidebar:
        st.write("**System Status:**")
        st.write(f"Active Operations: {system_status.get('active_operations', 0)}")
        st.write(f"System Health: {system_status.get('system_health', 'unknown')}")
        
        # Add emergency reset button
        if st.button("🔄 Reset System", help="Emergency reset if system is stuck"):
            from app.utils.robustness_integration import force_system_reset
            force_system_reset()
            st.rerun()
# --- Logging Setup ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create formatter
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(log_format)

# Main log handler - captures all levels (INFO, WARNING, ERROR, CRITICAL)
main_log_handler = logging.FileHandler(os.path.join(LOG_DIR, "log.log"))
main_log_handler.setLevel(logging.INFO)
main_log_handler.setFormatter(formatter)

# Error log handler - only captures ERROR and CRITICAL (no WARNING)
error_log_handler = logging.FileHandler(os.path.join(LOG_DIR, "errors.log"))
error_log_handler.setLevel(logging.ERROR)  # ERROR level = captures ERROR and CRITICAL only
error_log_handler.setFormatter(formatter)

# Console handler - captures all levels
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Configure root logger with all handlers
logging.basicConfig(
    level=logging.INFO,
    handlers=[main_log_handler, error_log_handler, console_handler]
)
# --- End Logging Setup ---

st.set_page_config(
    page_title="ValueRollerCoaster",
    page_icon="🎢",
    layout="wide",
    initial_sidebar_state="expanded"
)

import os
# Use append instead of insert to avoid path conflicts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import ensure_collections_exist, collection_exists
from app.ai.personas import build_buyer_persona
from app.components.value_components.value_components_tab import render_value_components_tab
from app.ui import show_main_ui  # show_main_ui is async and must be awaited with asyncio.run or similar
from app.components.help_modal import render_help_button
from app.core.company_context_manager import CompanyContextManager
from app.admin.company_setup_wizard import CompanySetupWizard

# --- Background Task Progress Indicator ---
def render_background_task_progress():
    """Show background task progress in sidebar with stable rendering to prevent duplicates."""
    try:
        from app.database import get_background_task, get_any_running_task_for_user
        
        task_id = st.session_state.get("background_persona_task_id")
        
        # If no task_id in session, try to find one in database
        if not task_id:
            try:
                user_id = st.session_state.get('user_id', 'anonymous')
                existing_task = asyncio.run(get_any_running_task_for_user(user_id))
                if existing_task:
                    task_id = existing_task.get("task_id")
                    if task_id:
                        st.session_state.background_persona_task_id = task_id
                    else:
                        return
                else:
                    return
            except Exception as e:
                logging.debug(f"Could not check for running tasks: {e}")
                return
        
        # Try to get task from database
        task = None
        try:
            task = asyncio.run(get_background_task(task_id))
        except RuntimeError as e:
            # Event loop already running - try alternative approach
            logging.debug(f"Event loop issue: {e}, showing initializing state")
            # Show "initializing" state if we can't query yet
            task = {"status": "running", "progress_percent": 0, "current_step": "Initializing..."}
        except Exception as e:
            logging.error(f"Error getting task {task_id}: {e}")
            # Show "initializing" state if task not found yet (might be just created)
            task = {"status": "running", "progress_percent": 0, "current_step": "Initializing..."}
        
        if not task:
            # Task not found - might be just created, show initializing state
            task = {"status": "running", "progress_percent": 0, "current_step": "Initializing..."}
        
        # CRITICAL: Use a single rendered flag per task_id to prevent duplicates
        # Only render progress display once per task_id per session
        rendered_key = f"progress_rendered_{task_id}"
        
        # Check if we've already rendered this task in this session
        # If yes, we still need to update the display, but we'll use placeholders
        if task["status"] == "running":
            # For running tasks, use placeholders that can be updated
            info_key = f"progress_info_{task_id}"
            progress_key = f"progress_bar_{task_id}"
            step_key = f"progress_step_{task_id}"
            percent_key = f"progress_percent_{task_id}"
            
            # Initialize placeholders only once
            if info_key not in st.session_state:
                st.session_state[info_key] = st.empty()
                st.session_state[progress_key] = st.empty()
                st.session_state[step_key] = st.empty()
                st.session_state[percent_key] = st.empty()
                st.session_state[rendered_key] = True
            
            # Update placeholders with current progress
            st.session_state[info_key].info(f"🔄 Generating persona...")
            st.session_state[progress_key].progress(task["progress_percent"] / 100)
            st.session_state[step_key].caption(f"Step: {task['current_step']}")
            st.session_state[percent_key].caption(f"Progress: {task['progress_percent']}%")
            
            # Less aggressive auto-refresh - only every 5 seconds and only if no user interaction
            import time
            current_time = time.time()
            last_refresh = st.session_state.get("last_sidebar_refresh", 0)
            user_interaction_time = st.session_state.get("last_user_interaction", 0)
            
            # Reset navigation_clicked flag after 2 seconds
            if st.session_state.get("navigation_clicked", False) and current_time - user_interaction_time > 2:
                st.session_state["navigation_clicked"] = False
            
            # Only auto-refresh if:
            # 1. It's been more than 5 seconds since last refresh
            # 2. No user interaction in the last 3 seconds
            # 3. No navigation buttons were clicked recently
            if (current_time - last_refresh > 5 and 
                current_time - user_interaction_time > 3 and
                not st.session_state.get("navigation_clicked", False)):
                st.session_state.last_sidebar_refresh = current_time
                st.rerun()
            
            # Add manual refresh button for user control
            if st.button("🔄 Refresh Progress", key=f"manual_progress_refresh_{task_id}", help="Manually refresh progress"):
                # CRITICAL: Clear cache to force fresh data fetch
                preserved_task_id = st.session_state.get("background_persona_task_id")
                if preserved_task_id:
                    # Clear the cached progress to force fresh fetch
                    cache_key = f"cached_progress_{preserved_task_id}"
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
                st.session_state.last_sidebar_refresh = 0  # Force refresh
                st.rerun()
            
        elif task["status"] == "completed":
            # Clear running task placeholders
            placeholder_keys = [
                f"progress_info_{task_id}",
                f"progress_bar_{task_id}",
                f"progress_step_{task_id}",
                f"progress_percent_{task_id}",
                f"progress_rendered_{task_id}"
            ]
            for key in placeholder_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Show completion status - only render once
            if not st.session_state.get(f"completion_shown_{task_id}", False):
                st.success("✅ Persona ready!")
                st.caption("Generation completed successfully")
                st.session_state[f"completion_shown_{task_id}"] = True
            
            # Update cache with completion status
            st.session_state[f"cached_progress_{task_id}"] = {
                "progress_percent": 100,
                "current_step": "✅ Completed",
                "status": "completed"
            }
            
            # CRITICAL: Always show the View Persona button when task is completed
            # Use a unique key based on task_id to prevent button duplication
            result_persona = task.get("result_persona")
            if result_persona:
                # Try multiple ways to get the ID
                persona_id = None
                if isinstance(result_persona, dict):
                    # Check top-level id
                    persona_id = result_persona.get("id")
                    # Check company.id as fallback
                    if not persona_id and isinstance(result_persona.get("company"), dict):
                        persona_id = result_persona["company"].get("id")
                
                if persona_id:
                    if st.button("👁️ View Persona", key=f"view_persona_button_{task_id}", type="primary", use_container_width=True):
                        st.session_state.selected_persona_id = persona_id
                        st.session_state["current_page"] = "Persona Generator"
                        # Clear task and flags after viewing
                        st.session_state.background_persona_task_id = None
                        if f"completion_shown_{task_id}" in st.session_state:
                            del st.session_state[f"completion_shown_{task_id}"]
                        st.rerun()
                else:
                    st.warning("⚠️ Persona ID not found. Please check Persona Search.")
            else:
                st.warning("⚠️ Persona data not available")
                
        elif task["status"] == "failed":
            # Clear running task placeholders
            placeholder_keys = [
                f"progress_info_{task_id}",
                f"progress_bar_{task_id}",
                f"progress_step_{task_id}",
                f"progress_percent_{task_id}",
                f"progress_rendered_{task_id}"
            ]
            for key in placeholder_keys:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.error(f"❌ Generation failed")
            st.caption(f"Error: {task.get('error_message', 'Unknown error')}")
            if st.button("Clear", key=f"clear_failed_task_{task_id}"):
                st.session_state.background_persona_task_id = None
                st.rerun()
                
    except Exception as e:
        logging.error(f"Error rendering background task progress: {e}")
        # Clear container on error
        task_id = st.session_state.get("background_persona_task_id")
        if task_id:
            container_key = f"progress_container_{task_id}"
            if container_key in st.session_state:
                del st.session_state[container_key]
        st.error("Error loading task progress")

# --- Sidebar and navigation logic (from main.py) ---
SIDEBAR_MENU = [
    {"label": "Value Components", "icon": "💎"},
    {"label": "Persona Generator", "icon": "👤"},
    {"label": "Persona Search", "icon": "🔍"},
    {"label": "API Chart", "icon": "📊"},
]

# --- Initialize all session state keys ---
if "current_page" not in st.session_state:
    st.session_state["current_page"] = SIDEBAR_MENU[0]["label"]
if "global_processing" not in st.session_state:
    st.session_state["global_processing"] = False
if "main_tab_selectbox" not in st.session_state:
    st.session_state["main_tab_selectbox"] = 0
if "main_tab_radio" not in st.session_state:
    st.session_state["main_tab_radio"] = 0
if "selected_main_category" not in st.session_state:
    st.session_state["selected_main_category"] = SIDEBAR_MENU[0]["label"]
if "selected_persona_id" not in st.session_state:
    st.session_state["selected_persona_id"] = None
if "background_persona_task_id" not in st.session_state:
    st.session_state["background_persona_task_id"] = None

with st.sidebar:
    st.markdown("# 🎢 Value Rollercoaster")
    
    
    st.markdown("---")
    nav_labels = [item["label"] for item in SIDEBAR_MENU]
    nav_icons = [item["icon"] for item in SIDEBAR_MENU]

    # Check if we should override navigation due to persona selection FIRST
    if st.session_state.get("selected_persona_id"):
        st.session_state["current_page"] = "Persona Generator"
    
    # Track which button is clicked in this run
    selected_nav = st.session_state.get("current_page", nav_labels[0])
    
    for label, icon in zip(nav_labels, nav_icons):
        if st.button(f"{icon}  {label}", use_container_width=True, key=f"nav_btn_{label}"):
            # Track user interaction to prevent auto-refresh
            import time
            st.session_state["last_user_interaction"] = time.time()
            st.session_state["navigation_clicked"] = True
            
            # Don't override if we have a persona selected
            if not st.session_state.get("selected_persona_id"):
                selected_nav = label
                # Update session state immediately
                st.session_state["current_page"] = label
                # Clear persona selection when manually navigating
                if label != "Persona Generator":
                    st.session_state["selected_persona_id"] = None
            # Reset value category to Summary when Value Components is clicked
            if label == "Value Components":
                st.session_state["main_tab_selectbox"] = 0
                st.session_state["main_tab_radio"] = 0
                st.session_state["selected_main_category"] = "Summary"
                # Force selectbox to reset by changing its key
                st.session_state["selectbox_reset_key"] = st.session_state.get("selectbox_reset_key", 0) + 1
            # Force rerun to ensure dropdown visibility updates immediately
            st.rerun()
        
        # Show Value Category dropdown right after Value Components button
        if label == "Value Components":
            # Only show dropdown if we're currently on Value Components page
            if st.session_state.get("current_page") == "Value Components":
                from app.categories import COMPONENT_STRUCTURES
                main_category_labels = ["Summary"] + list(COMPONENT_STRUCTURES.keys())
                main_category_icons = ["🧮"] + [COMPONENT_STRUCTURES[cat]["icon"] for cat in COMPONENT_STRUCTURES.keys()]
                menu_options = [f"{icon} {cat}" for icon, cat in zip(main_category_icons, main_category_labels)]
                # --- Spinner for category change ---
                prev_idx = st.session_state.get("main_tab_selectbox", 0)
                reset_key = st.session_state.get("selectbox_reset_key", 0)
                selected_idx = st.selectbox(
                    "Value Category",
                    options=list(range(len(main_category_labels))),
                    format_func=lambda i: menu_options[i],
                    index=prev_idx,
                    key=f"main_tab_selectbox_{reset_key}"
                )
                if selected_idx != prev_idx:
                    # Update session state for category change
                    st.session_state["main_tab_radio"] = selected_idx
                    st.session_state["selected_main_category"] = main_category_labels[selected_idx]
                    st.rerun()
                else:
                    # Update session state even if no change (for consistency)
                    st.session_state["main_tab_radio"] = selected_idx
                    st.session_state["selected_main_category"] = main_category_labels[selected_idx]
                
                # Add separation line after the dropdown
                st.markdown("---")
    
    # Help button
    st.markdown("---")
    render_help_button()
    
    # Background task progress indicator - REMOVED from sidebar
    # Progress is now shown on the main Persona Generator page for better UX
    # Sidebar navigation buttons are disabled during generation (handled in navigation logic)


# Company setup is now handled through admin interface
# No automatic wizard trigger

current_page = st.session_state["current_page"]

# Render help modal if needed

import asyncio
asyncio.run(show_main_ui(current_page)) 