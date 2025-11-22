import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import streamlit as st
import asyncio
import logging

logger = logging.getLogger(__name__)
from app.database import save_persona, get_personas, get_persona_by_id, delete_persona_by_id, GENERATOR_VERSION
from app.ai.personas import build_buyer_persona
from app.utils.spinner import save_spinner, generate_spinner, dialog_spinner
from app.utils.spinner.persona_generation_spinner import persona_generation_spinner, update_persona_progress
import app.utils as utils
import plotly.graph_objects as go
from streamlit_extras.badges import badge
from app.components.value_alignment_display import display_advanced_value_alignment
import time
from qdrant_client import QdrantClient
from app.config import DEBUG_MODE, DEBUG_AI_PROCESSING
from app.components.demo_companies import DemoIntegration
from typing import Tuple, Optional


def check_background_task_running() -> Tuple[bool, Optional[str]]:
    """
    Check if any background task is running for the current user.
    Centralized function to check running tasks consistently across all components.
    
    This function is optimized to:
    1. First check session state (fastest)
    2. Then verify with database if needed
    3. Always ensure background_persona_task_id is set for sidebar progress
    
    Returns:
        Tuple of (is_running: bool, running_website: Optional[str])
    """
    # First check session state - fastest path
    task_id_in_session = st.session_state.get("background_persona_task_id")
    
    # If we have task_id, verify it's still running
    if task_id_in_session:
        try:
            from app.database import get_background_task
            # Use new_event_loop() to avoid conflicts with existing async context
            import asyncio
            try:
                # Check if we're in an async context
                loop = asyncio.get_running_loop()
                # We're in async - can't use asyncio.run(), assume running based on task_id
                logger.debug(f"In async context, using session state task_id {task_id_in_session}")
                return True, None
            except RuntimeError:
                # No running loop - safe to use asyncio.run()
                task = asyncio.run(get_background_task(task_id_in_session))
                
                if task and task.get("status") == "running":
                    return True, task.get("website", "unknown")
                elif task and task.get("status") == "completed":
                    # Task completed - clear it
                    st.session_state.background_persona_task_id = None
                    return False, None
                elif task and task.get("status") == "failed":
                    # Task failed - clear it
                    st.session_state.background_persona_task_id = None
                    return False, None
                elif task is None:
                    # Task doesn't exist in database - but don't clear immediately
                    # It might be a timing issue. Only clear if we're sure it's not running
                    # For now, preserve task_id and assume it's running (safer approach)
                    logger.warning(f"Task {task_id_in_session} not found in database, but preserving task_id in session")
                    return True, None
                else:
                    # Task has other status - preserve task_id and assume running
                    # This handles edge cases where status might be temporarily unavailable
                    logger.debug(f"Task {task_id_in_session} has status {task.get('status')}, preserving task_id")
                    return True, None
        except Exception as e:
            logger.debug(f"Could not verify task {task_id_in_session}: {e}")
            # If we can't verify but have task_id, assume it's running
            # This is safer - don't clear on errors as it might be temporary
            return True, None
    
    # No task_id in session - check database for any running tasks
    try:
        from app.database import get_any_running_task_for_user
        
        user_id = st.session_state.get('user_id', 'anonymous')
        
        # Check if we're in async context
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # We're in async context - can't use asyncio.run()
            # Return False for now (async caller should handle this differently)
            logger.debug("In async context, cannot query database here")
            return False, None
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            existing_task = asyncio.run(get_any_running_task_for_user(user_id))
            
            if existing_task:
                # Found a running task - store task_id in session state for sidebar
                task_id = existing_task.get("task_id")
                if task_id:
                    st.session_state.background_persona_task_id = task_id
                
                return True, existing_task.get("website", "unknown")
        
        return False, None
        
    except Exception as e:
        logger.warning(f"Could not check for running task: {e}")
        # On error, if we have task_id, assume it's running
        if task_id_in_session:
            return True, None
        return False, None


async def run_build_buyer_persona(website, selected_industry, progress_tracker=None):
    # Use the new enhanced pipeline for persona generation
    try:
        persona = await build_buyer_persona(website, selected_industry, progress_tracker=progress_tracker)
        
        # Check if persona generation failed
        if isinstance(persona, dict):
            if "error" in persona and len(persona) == 1:
                # This is a pure error object, log it
                logging.error(f"[run_build_buyer_persona] Persona generation error: {persona['error']}")
                return persona
            elif "error" in persona and "company" in persona:
                # This is a fallback persona with error info, log the error but return the persona
                logging.warning(f"[run_build_buyer_persona] Using fallback persona due to error: {persona['error']}")
                return persona
            else:
                # This is a successful persona
                return persona
        
        return persona
    except Exception as e:
        logging.error(f"[run_build_buyer_persona] Exception: {e}")
        return {"error": f"Exception during persona generation: {e}"}

async def display_persona_details(persona: dict, generator_version: Optional[str] = None):
    """Display a buyer persona in a tabbed interface."""
    
    def get_model_indicator(field_name: str, persona: dict, is_enhanced: bool) -> str:
        """Get model indicator for a specific field."""
        if not is_enhanced:
            return ""
        
        # Determine which model primarily generated this field
        if field_name in ["product_range", "services", "goals", "value_drivers", "value_signals"]:
            return "🔵 *Generated by Gemini*"
        elif field_name in ["creative_elements", "innovative_insights", "emotional_factors"]:
            return "🟢 *Generated by ChatGPT*"
        else:
            return "🤖 *Dual-Model (Validated)*"
    
    # Robustly detect if this is a saved persona (from DB)
    is_saved_persona = False
    if "persona" in persona:
        loaded_version = persona.get("generator_version")
        persona = persona["persona"]
        is_saved_persona = True
    elif persona.get("id") or persona.get("scan_date"):
        is_saved_persona = True
        loaded_version = persona.get("generator_version")
    else:
        loaded_version = generator_version

    # --- Check if background task is running ---
    background_task_running, running_website = check_background_task_running()
    
    # --- Buttons moved to inline with title ---
    if st.session_state.get("selected_persona_id"):
        # Show Back to Search button for saved personas
        if st.button("⬅️ Back to Search", key="details_back_to_search_anywhere", 
                     disabled=background_task_running,
                     help="Return to persona search" if not background_task_running else "Cannot navigate during generation"):
            st.session_state.selected_persona_id = None
            st.session_state["current_page"] = "Persona Search"
            st.session_state["came_from_search"] = False  # Reset navigation context
            if "persona" in st.session_state:
                del st.session_state["persona"]
            if "website_input" in st.session_state:
                st.session_state.website_input = ""
            st.session_state.status_checked = False
            st.rerun()
    else:
        # Show Save and Clear buttons for new personas
        # Only show Save/Clear buttons for new (not already saved) personas
        if 'persona_saved' not in st.session_state:
            st.session_state.persona_saved = False
        
        # Buttons are now inline with the title above
        
        # Show confirmation dialog if needed
        if st.session_state.get("show_clear_confirmation", False):
            st.warning("⚠️ **Are you sure you want to clear this persona?**")
            st.info("This will remove the current persona and reset the form. This action cannot be undone.")
            
            col_confirm, col_cancel = st.columns([1, 1])
            with col_confirm:
                if st.button("✅ Yes, Clear Persona", key="confirm_clear_persona"):
                    # Clear all persona-related session state
                    if "persona" in st.session_state:
                        del st.session_state["persona"]
                    if "persona_saved" in st.session_state:
                        del st.session_state["persona_saved"]
                    if "generated_persona" in st.session_state:
                        del st.session_state["generated_persona"]
                    if "generator_version" in st.session_state:
                        del st.session_state["generator_version"]
                    if "generation_success_time" in st.session_state:
                        del st.session_state["generation_success_time"]
                    
                    # Clear the website input
                    st.session_state.clear_input_on_next_run = True
                    
                    # Reset confirmation state
                    st.session_state.show_clear_confirmation = False
                    
                    st.toast("🗑️ Persona cleared successfully!", icon="🗑️")
                    st.rerun()
            
            with col_cancel:
                if st.button("❌ Cancel", key="cancel_clear_persona"):
                    st.session_state.show_clear_confirmation = False
                    st.rerun()

    # Check for demo persona using multiple indicators
    is_demo_persona = (
        isinstance(persona, dict) and (
            persona.get("demo_mode", False) or 
            persona.get("demo_customer_name") or 
            persona.get("generation_time") or
            persona.get("demo_customer_id")
        )
    )
    
    if is_demo_persona:
        st.info(f"🎭 **Demo Mode** - This is a demo persona for {persona.get('demo_customer_name', 'Unknown')}")
        st.caption(f"Generated in {persona.get('generation_time', 0):.2f} seconds using pre-built customer data")
        
        # Add Demo Mode action buttons
        col_go_back, col_delete = st.columns([1, 1])
        
        with col_go_back:
            # Check background task for demo buttons too
            demo_background_running, _ = check_background_task_running()
            
            if st.button("🔙 Go Back to Generator", key="demo_go_back_details", 
                        disabled=demo_background_running,
                        help="Return to the persona generator" if not demo_background_running else "Cannot navigate during generation"):
                # Clear demo persona from session state
                st.session_state.persona = None
                st.session_state.selected_persona_id = None
                st.session_state.demo_mode_active = False
                st.session_state.demo_progress = 0
                st.session_state.demo_current_step = ""
                st.rerun()
        
        with col_delete:
            if st.button("🗑️ Delete Demo", key="demo_delete_details_button", 
                        disabled=demo_background_running,
                        help="Delete this demo persona" if not demo_background_running else "Cannot delete during generation"):
                # Store deletion result in session state to persist across reloads
                st.session_state.demo_delete_result = None
                st.session_state.demo_delete_error = None
                
                # Delete demo persona from database if it has an ID
                persona_id = persona.get("id")
                
                if persona_id:
                    try:
                        # Create a synchronous delete function to avoid asyncio issues
                        from qdrant_client import QdrantClient
                        from qdrant_client.models import Filter, FieldCondition, MatchValue, PointIdsList, UpdateStatus
                        from app.database import QDRANT_CLIENT, PERSONA_COLLECTION, VECTOR_DIM
                        
                        # Get user ID for ownership check
                        user_id = st.session_state.get('user_id', 'default_user')
                        
                        # Check if persona exists and belongs to user
                        filter_conditions = [
                            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
                            FieldCondition(key="id", match=MatchValue(value=persona_id))
                        ]
                        
                        results = QDRANT_CLIENT.search(
                            collection_name=PERSONA_COLLECTION,
                            query_vector=[0.0] * VECTOR_DIM,  # Dummy vector for filtering
                            query_filter=Filter(must=filter_conditions),  # type: ignore[arg-type]
                            limit=1,
                            with_payload=False
                        )
                        
                        if not results:
                            st.session_state.demo_delete_result = "not_found"
                        else:
                            # Delete the persona
                            response = QDRANT_CLIENT.delete(
                                collection_name=PERSONA_COLLECTION,
                                points_selector=PointIdsList(points=[persona_id]),
                            )
                            if response.status == UpdateStatus.COMPLETED:
                                st.session_state.demo_delete_result = "success"
                            else:
                                st.session_state.demo_delete_result = "error"
                                st.session_state.demo_delete_error = f"Failed to delete persona. Status: {response.status}"
                    except Exception as e:
                        st.session_state.demo_delete_error = str(e)
                        st.session_state.demo_delete_result = "error"
                else:
                    st.session_state.demo_delete_result = "no_id"
                
                # Clear demo persona from session state
                st.session_state.persona = None
                st.session_state.selected_persona_id = None
                st.session_state.demo_mode_active = False
                st.session_state.demo_progress = 0
                st.session_state.demo_current_step = ""
                st.rerun()
        
        # Show deletion result if available
        if st.session_state.get("demo_delete_result"):
            if st.session_state.demo_delete_result == "success":
                st.success("✅ Demo persona deleted successfully!")
            elif st.session_state.demo_delete_result == "not_found":
                st.warning("⚠️ Demo persona may not have been in database")
            elif st.session_state.demo_delete_result == "error":
                st.error(f"❌ Could not delete from database: {st.session_state.demo_delete_error}")
            elif st.session_state.demo_delete_result == "no_id":
                st.warning("⚠️ Demo persona has no ID - cannot delete from database")
            
            # Clear the result after showing it
            st.session_state.demo_delete_result = None
            st.session_state.demo_delete_error = None
        
        st.markdown("---")  # Add separator before persona content
    else:
        # Add header for normal (non-demo) personas
        # Get generation date and user display name
        generation_date = persona.get("created_at") or persona.get("scan_date") or "Unknown date"
        display_name = persona.get("created_by_display_name") or persona.get("user_id") or "Unknown user"
        
        # Format the date nicely
        if generation_date != "Unknown date":
            try:
                from datetime import datetime
                if isinstance(generation_date, str):
                    # Try to parse the date string (handle multiple formats)
                    try:
                        parsed_date = datetime.fromisoformat(generation_date.replace('Z', '+00:00'))
                    except:
                        # Try parsing without timezone
                        parsed_date = datetime.fromisoformat(generation_date.split('+')[0].split('Z')[0])
                    formatted_date = parsed_date.strftime("%B %d, %Y at %I:%M %p")
                else:
                    formatted_date = str(generation_date)
            except Exception as e:
                logger.warning(f"Could not parse date {generation_date}: {e}")
                formatted_date = str(generation_date)
        else:
            formatted_date = "Unknown date"
        
        # Display header for normal persona
        st.markdown(f"**Buyer Persona** - Generated on {formatted_date}")
        st.caption(f"Created by: {display_name}")
        
        
        st.markdown("---")  # Add separator before persona content

    # Check if this is an enhanced persona
    is_enhanced = persona.get("enhanced_metadata", {}).get("generation_method") == "dual_model_enhanced"
    
    # Add spacing between header and content below
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if is_enhanced:
        # Show enhanced UI with confidence score
        confidence = persona.get("enhanced_metadata", {}).get("confidence_score", 75)
        st.markdown(f'<h3 style="color: rgb(136, 136, 136);">🎯 Analysis Confidence: {confidence}%</h3>', unsafe_allow_html=True)
        
        tab_titles = [
            "Company Overview", 
            "Profile", 
            "Value Alignment",
            "Industry Context", 
            "AI Insights"
        ]
    else:
        # Show legacy UI
        tab_titles = [
            "Company Overview", 
            "Profile", 
            "Value Alignment",
            "Industry Context", 
            "AI Insights"
        ]
    tabs = st.tabs(tab_titles)

    # Tab 1: Company Overview
    with tabs[0]:
        st.subheader("Company Information")
        
        # Create three columns for company info, sunburst chart, and legend
        # Adjusted ratios: company info (1), sunburst chart (2), legend (0.5)
        col_company, col_sunburst, col_legend = st.columns([1, 2.3, 0.6])
        
        with col_company:
            company_data = persona.get("company", {})

            # Fallback logic for backward compatibility
            company_name = company_data.get("name") or persona.get("company_name") or persona.get("name")
            year_established = company_data.get("year_established") or persona.get("year_established")
            location = company_data.get("headquarters_location") or persona.get("headquarters_location") or persona.get("contact_information", {}).get("address")
            website = company_data.get("website") or persona.get("website")
            industry = persona.get("industry")

            if company_name:
                st.write(f"**Name:** {company_name}")
            if year_established:
                st.write(f"**Year Established:** {year_established}")
            if location:
                st.write(f"**Location:** {location}")
            if industry:
                st.write(f"**Industry:** {industry}")

            if website:
                if not website.startswith("http"):
                    website = f"https://{website}"
                st.write(f"**Website:** [{website}]({website})")
            
            # Enhanced confidence score display
            if is_enhanced:
                st.markdown("---")
                enhanced_metadata = persona.get("enhanced_metadata", {})
                confidence = enhanced_metadata.get("confidence_score", 75)
                
                st.markdown("**🎯 Analysis Confidence:**")
                if confidence >= 80:
                    st.success(f"**{confidence}%** - High Confidence")
                elif confidence >= 60:
                    st.warning(f"**{confidence}%** - Medium Confidence")
                else:
                    st.error(f"**{confidence}%** - Low Confidence")
                
                # Confidence breakdown
                col_conf1, col_conf2, col_conf3 = st.columns(3)
                with col_conf1:
                    st.metric("Model Agreement", f"{confidence}%")
                with col_conf2:
                    st.metric("Data Quality", f"{min(confidence + 5, 100)}%")
                with col_conf3:
                    web_search_enabled = enhanced_metadata.get("web_search_enabled", True)
                    st.metric("Web Search", "✅" if web_search_enabled else "❌")
        
        with col_sunburst:
            # Add spacing before sunburst chart
            #st.markdown("<br>", unsafe_allow_html=True)
            
            # Add sunburst chart to Company Overview tab
            playbook_data = persona.get("advanced_value_alignment") or {}
            alignment_matrix = playbook_data.get("alignment_matrix") or []
            
            # Debug: Log persona structure
            logger.warning(f"[persona_tab.py] Persona demo_mode: {persona.get('demo_mode', False)}")
            logger.warning(f"[persona_tab.py] Persona id: {persona.get('id', 'no_id')}")
            logger.warning(f"[persona_tab.py] Alignment matrix length: {len(alignment_matrix) if alignment_matrix else 0}")
            
            if alignment_matrix:
                st.markdown("**📊 Value Alignment Overview**")
                
                # Use the same alignment chart for both demo and real personas
                from app.components.value_alignment.sunburst_overview import render_sunburst_overview
                render_sunburst_overview(alignment_matrix)
            else:
                st.info("No value alignment data available.")
        
        with col_legend:
            # Sunburst Legend (top-right corner)
            with st.expander("📊 Chart Legend", expanded=False):
                st.markdown("""
                    <div style="color: rgb(128, 132, 149); font-size: 14px;">
                    <h4>🌞 Sunburst Elements</h4>
                    <ul>
                    <li><strong>Colors:</strong> Different value categories</li>
                    <li><strong>Inner Ring:</strong> Value Alignment root</li>
                    <li><strong>Middle Ring:</strong> Value categories</li>
                    <li><strong>Outer Ring:</strong> Customer needs & components</li>
                    <li><strong>%:</strong> Alignment score proportion</li>
                    </ul>
                    
                    <h4>💡 How to read:</h4>
                    <ul>
                    <li>Hover for full details</li>
                    <li>Larger segments = higher importance</li>
                    </ul>
                    </div>
                """, unsafe_allow_html=True)

    # Tab 2: Profile
    with tabs[1]:
        
        # Get data for all three columns
        products = persona.get("product_range", [])
        services = persona.get("services", [])
        goals = persona.get("goals", [])
        value_drivers = persona.get("value_drivers", [])
        value_signals = persona.get("value_signals", [])
        pain_points = persona.get("pain_points", [])
        likely_objections = persona.get("likely_objections", [])
        
        # Check if we have data for any column
        has_offerings_needs = products or services
        has_strategy = goals or value_drivers or value_signals
        has_hot_spots = pain_points or likely_objections
        
        if has_offerings_needs or has_strategy or has_hot_spots:
            # Create three columns for side-by-side display
            col1, col2, col3 = st.columns(3)
            
            # Left column: Offerings & Needs
            with col1:
                if has_offerings_needs:
                    st.markdown("### 🏭 Offerings & Needs")
                    
                    if products:
                        with st.expander("📦 Product Range", expanded=False):
                            # Add model indicator for enhanced personas
                            if is_enhanced:
                                st.markdown("🔵 *Generated by Gemini*")
                            
                            if isinstance(products, str):
                                st.markdown(products)
                            elif isinstance(products, list):
                                for product in products:
                                    st.markdown(f"• {product}")
                            else:
                                st.markdown(str(products))
                    
                    if services:
                        with st.expander("🛠️ Services", expanded=False):
                            # Add model indicator for enhanced personas
                            if is_enhanced:
                                st.markdown("🔵 *Generated by Gemini*")
                            
                            if isinstance(services, str):
                                st.markdown(services)
                            elif isinstance(services, list):
                                for service in services:
                                    st.markdown(f"• {service}")
                            else:
                                st.markdown(str(services))
                else:
                    st.markdown("### 🏭 Offerings & Needs")
                    st.info("No offerings and needs data available.")
            
            # Middle column: Strategy
            with col2:
                if has_strategy:
                    st.markdown("### 🧭 Strategy")
                    
                    if goals:
                        with st.expander("🎯 Company Goals", expanded=False):
                            # Add model indicator for enhanced personas
                            if is_enhanced:
                                st.markdown("🔵 *Generated by Gemini*")
                            
                            if isinstance(goals, str):
                                st.markdown(goals)
                            elif isinstance(goals, list):
                                for goal in goals:
                                    st.markdown(f"• {goal}")
                            else:
                                st.markdown(str(goals))
                    
                    if value_drivers:
                        with st.expander("🚀 Value Drivers", expanded=False):
                            if isinstance(value_drivers, str):
                                st.markdown(value_drivers)
                            elif isinstance(value_drivers, list):
                                for driver in value_drivers:
                                    if isinstance(driver, dict):
                                        display_text = driver.get("name", str(driver))
                                        st.markdown(f"• {display_text}")
                                    else:
                                        st.markdown(f"• {driver}")
                            else:
                                st.markdown(str(value_drivers))
                    
                    if value_signals:
                        with st.expander("📡 Value Signals", expanded=False):
                            if isinstance(value_signals, str):
                                st.markdown(value_signals)
                            elif isinstance(value_signals, list):
                                for signal in value_signals:
                                    st.markdown(f"• {signal}")
                            else:
                                st.markdown(str(value_signals))
                else:
                    st.markdown("### 🧭 Strategy")
                    st.info("No strategy data available.")
            
            # Right column: Hot Spots
            with col3:
                if has_hot_spots:
                    st.markdown("### 🔥 Hot Spots")
                    
                    if pain_points:
                        with st.expander("⚡ Pain Points", expanded=False):
                            # Add model indicator for enhanced personas
                            if is_enhanced:
                                st.markdown("🔵 *Generated by Gemini*")
                            
                            if isinstance(pain_points, str):
                                st.markdown(pain_points)
                            elif isinstance(pain_points, list):
                                for pain in pain_points:
                                    st.markdown(f"• {pain}")
                            else:
                                st.markdown(str(pain_points))
                    
                    if likely_objections:
                        with st.expander("🚫 Likely Objections", expanded=False):
                            if isinstance(likely_objections, str):
                                st.markdown(likely_objections)
                            elif isinstance(likely_objections, list):
                                for obj in likely_objections:
                                    st.markdown(f"• {obj}")
                            else:
                                st.markdown(str(likely_objections))
                else:
                    st.markdown("### 🔥 Hot Spots")
                    st.info("No hot spots data available.")
        
        # Fallback if no data available
        elif not has_offerings_needs and not has_strategy and not has_hot_spots:
            st.info("No profile data available.")
        
        # Creative Elements section removed as requested

    # Tab 3: Value Alignment
    with tabs[2]:
        playbook_data = persona.get("advanced_value_alignment") or {}
        alignment_matrix = playbook_data.get("alignment_matrix") or []

        # --- Value Alignment Radar Chart ---
        if alignment_matrix:
            st.markdown("### 📊 Value Alignment Overview")
            
            # Add model indicator for enhanced personas
            if is_enhanced:
                st.markdown("🔵 *Generated by Gemini*")
            
            from app.components.value_alignment.radar_overview import render_radar_overview
            render_radar_overview(alignment_matrix)
            st.divider()

        # --- Grouped Expanders for Alignment Matrix ---
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

        def get_value_category_indicators(value_component):
            """Get color indicators for value categories based on database lookup (source of truth)"""
            from app.database import fetch_all_value_components
            from app.components.demo_companies.demo_profile_manager import demo_profile_manager
            from app.components.value_alignment.component_lookup import get_category_indicator_from_db
            
            # Try to find component in database first (same method as sunburst chart)
            try:
                user_id = demo_profile_manager.get_current_user_id()
                all_db_components = fetch_all_value_components(user_id=user_id)
                
                # Use shared lookup utility
                indicator = get_category_indicator_from_db(value_component, all_db_components)
                if indicator:
                    return indicator
            except Exception as e:
                logger.warning(f"[persona_tab] Failed to lookup component '{value_component}' in DB: {e}. Using fallback.")
            
            # Fallback: if not found in DB, log warning and use keyword matching as last resort
            logger.warning(f"[persona_tab] Component '{value_component}' not found in database. Using fallback keyword matching.")
            component_lower = value_component.lower()
            
            # Fallback keyword matching (same logic as before, but as last resort only)
            if any(word in component_lower for word in ['technical value', 'quality', 'performance', 'reliability', 'certificate', 'compliance', 'testing', 'speed', 'efficiency', 'scalability', 'circular economy', 'innovation', 'technology']):
                return '🔵'
            elif any(word in component_lower for word in ['business value', 'cost', 'savings', 'roi', 'productivity', 'optimization', 'revenue', 'profit', 'market access', 'operational']):
                return '🟣'
            elif any(word in component_lower for word in ['strategic value', 'strategy', 'competitive', 'leadership', 'differentiation', 'growth', 'expansion', 'positioning']):
                return '🔴'
            elif any(word in component_lower for word in ['after sales value', 'after sales', 'support', 'service', 'maintenance', 'training', 'consulting', 'warranty', 'help', 'availability', 'responsiveness']):
                return '🟠'
            
            # Default fallback
            return '🔵'

        high, medium, low = group_by_score(alignment_matrix)
        
        # Compact legend for right corner
        legend_html = """
        <div style="position: absolute; top: 0; right: 0; font-size: 11px; color: #666; background: rgba(255,255,255,0.9); padding: 4px 8px; border-radius: 4px;">
        🔵 Technical | 🟣 Business | 🔴 Strategic | 🟠 After Sales
        </div>
        """
        
        def match_expander(idx, item, default_expanded=False):
            need = item.get('prospect_need') or item.get('customer_need', 'N/A')
            value_component = item.get('our_value_component', 'N/A')
            score = item.get('match_score_percent', 0)
            rationale = item.get('rationale', 'No rationale provided.')
            conversation = item.get('conversation_starter')
            
            # Get value category indicators
            indicators = get_value_category_indicators(value_component)
            
            # Create expander title with indicators
            expander_title = f"{need} ({score}%) {indicators}"
            
            with st.expander(expander_title, expanded=default_expanded):
                st.markdown(f"**Customer Need / Goal:** <span style='color:#1976D2'>{need}</span>", unsafe_allow_html=True)
                st.markdown(f"**Matched Value Component:** <span style='color:#388E3C'>{value_component}</span>", unsafe_allow_html=True)
                
                # Enhanced match score indicator
                if score >= 95:
                    level = "Excellent Match"
                elif score >= 70:
                    level = "Good Match"
                else:
                    level = "Weak Match"
                
                st.markdown(f"**Alignment Strength:** <span style='color:#1976D2;font-weight:bold'>{level} ({score}%)</span>", unsafe_allow_html=True)
                
                st.markdown(f"**Rationale:** {rationale}")
                if conversation:
                    st.info(f"💬 **Conversation Starter:** {conversation}")

        def section_header(title, icon):
            st.markdown(f"<h4 style='margin-top:1.5em'>{icon} {title}</h4>", unsafe_allow_html=True)

        if alignment_matrix:
            # Add legend to right corner
            st.markdown(legend_html, unsafe_allow_html=True)
            
            # Create two columns for High and Medium alignment
            col_high, col_medium = st.columns(2)
            
            # Left column: High Alignment
            with col_high:
                section_header("High Alignment (≥ 95%)", "💎")
                if high:
                    for idx, item in high:
                        match_expander(idx, item, default_expanded=False)
                else:
                    st.caption("No high alignment needs.")
            
            # Right column: Medium Alignment
            with col_medium:
                section_header("Medium Alignment (94–70%)", "🎲")
                if medium:
                    for idx, item in medium:
                        match_expander(idx, item, default_expanded=False)
                else:
                    st.caption("No medium alignment needs.")
            
            # Low alignment below in full width
            # section_header("Low Alignment (< 70%)", "⚠️")
            # if low:
            #     for idx, item in low:
            #         match_expander(idx, item, default_expanded=False)
            # else:
            #     st.caption("No low alignment needs.")
        else:
            st.info("No value alignment data available.")

    # Tab 4: Industry Context
    with tabs[3]:
        # Industry Context header removed as requested
        
        # Get industry context data
        industry_ctx = persona.get("industry_context", {})
        market_intelligence = persona.get("market_intelligence", {})
        
        
        # Also check for market intelligence in other possible locations
        if not market_intelligence:
            market_intelligence = persona.get("market_data", {})
        
        # Check for full market intelligence data
        full_market_intelligence = persona.get("full_market_intelligence", {})
        if full_market_intelligence and isinstance(full_market_intelligence, dict):
            market_intelligence = full_market_intelligence
        
        # For enhanced personas, the market intelligence might be nested
        if is_enhanced and isinstance(market_intelligence, dict):
            # Try to get the actual market intelligence data from the nested structure
            if "market_intelligence" in market_intelligence:
                market_intelligence = market_intelligence["market_intelligence"]
                if DEBUG_MODE or DEBUG_AI_PROCESSING:
                    print(f"DEBUG: Found nested market intelligence, keys: {list(market_intelligence.keys()) if isinstance(market_intelligence, dict) else 'Not a dict'}")
            elif "base_intelligence" in market_intelligence:
                base_intel = market_intelligence["base_intelligence"]
                if isinstance(base_intel, dict) and "market_intelligence" in base_intel:
                    market_intelligence = base_intel["market_intelligence"]
                    if DEBUG_MODE or DEBUG_AI_PROCESSING:
                        print(f"DEBUG: Found market intelligence in base_intelligence, keys: {list(market_intelligence.keys()) if isinstance(market_intelligence, dict) else 'Not a dict'}")
        
        if DEBUG_MODE or DEBUG_AI_PROCESSING:
            print(f"DEBUG: Final market intelligence type: {type(market_intelligence)}")
            if isinstance(market_intelligence, dict):
                print(f"DEBUG: Final market intelligence keys: {list(market_intelligence.keys())}")
        
        # Industry Overview section removed as requested (Gemini part)
        
        # Create 2-column layout for Market Intelligence
        has_market_intelligence = market_intelligence and isinstance(market_intelligence, dict)
        
        if has_market_intelligence:
            # Separation line removed as requested
            
            # Show only Market Intelligence (single column layout)
            st.markdown("### 📊 Market Intelligence")
            
            # Market Overview
            market_overview = market_intelligence.get("market_overview", {})
            if market_overview:
                with st.expander("📈 Market Overview", expanded=False):
                    if market_overview.get("market_size"):
                        size_data = market_overview["market_size"]
                        st.metric("Global Market Size", size_data.get("global", "N/A"))
                        st.metric("European Market Size", size_data.get("european", "N/A"))
                    if market_overview.get("growth_rate"):
                        st.metric("Growth Rate", market_overview["growth_rate"])
                    if market_overview.get("projection_5y"):
                        st.metric("5-Year Projection", market_overview["projection_5y"])
                    
                    if market_overview.get("key_segments"):
                        st.markdown("**Key Market Segments:**")
                        for segment in market_overview["key_segments"]:
                            st.markdown(f"• {segment}")
            
            # Current Trends
            current_trends = market_intelligence.get("current_trends", [])
            if current_trends:
                with st.expander("🔄 Current Trends", expanded=False):
                    for trend in current_trends:
                        impact_emoji = "🔴" if trend.get("impact") == "High" else "🟡" if trend.get("impact") == "Medium" else "🟢"
                        st.markdown(f"**{impact_emoji} {trend.get('trend', 'N/A')}**")
                        st.markdown(f"*{trend.get('description', 'N/A')}*")
                        if trend.get("business_implications"):
                            st.markdown(f"**Business Impact:** {trend['business_implications']}")
                        st.markdown("---")
            
            # Competitive Landscape
            competitive = market_intelligence.get("competitive_landscape", {})
            if competitive:
                with st.expander("🏆 Competitive Landscape", expanded=False):
                    if competitive.get("key_competitors"):
                        st.markdown("**Key Competitors:**")
                        for competitor in competitive["key_competitors"]:
                            st.markdown(f"**{competitor.get('name', 'N/A')}**")
                            st.markdown(f"*{competitor.get('positioning', 'N/A')}*")
                            if competitor.get("market_share"):
                                st.markdown(f"Market Share: {competitor['market_share']}")
                            st.markdown("---")
                    
                    if competitive.get("competitive_advantages"):
                        st.markdown("**Competitive Advantages:**")
                        for advantage in competitive["competitive_advantages"]:
                            st.markdown(f"• {advantage}")
        
        # Fallback if no market intelligence data
        else:
            st.info("No industry context data available.")

        st.markdown("""
        <style>
        .element-container .stAlert {
            background-color: #f5f7fa;
            border-left: 5px solid #4F8BF9;
            font-size: 1.1em;
            margin-top: 1em;
            margin-bottom: 1em;
        }
        </style>
        """, unsafe_allow_html=True)

    # Tab 5: AI Insights (or Tab 4 for legacy personas)
    tab_index = 4 if is_enhanced else 4
    with tabs[tab_index]:
        st.subheader("AI Reasoning: Chain of Thought")
        
        # Add model indicator for enhanced personas
        if is_enhanced:
            st.markdown("🔵 *Generated by Gemini*")
        playbook_data = persona.get("advanced_value_alignment") or {}

        if not playbook_data or "error" in playbook_data:
            st.warning("Advanced value alignment could not be generated.")
            if playbook_data.get("error"):
                st.error(f"Reason: {playbook_data.get('error')}")
        else:
            # Prefer new reasoning_steps if available
            reasoning_steps = playbook_data.get("reasoning_steps")
            if reasoning_steps and isinstance(reasoning_steps, list):
                for step in reasoning_steps:
                    with st.expander(f"Step {step.get('step', '?')}: {step.get('title', '')}", expanded=False):
                        # Custom rendering for Final Aligner step
                        if step.get('title', '').lower().startswith('final aligner'):
                            alignment_matrix = playbook_data.get('alignment_matrix', [])
                            def strength_label(score):
                                if score is None:
                                    return 'N/A'
                                if score >= 90:
                                    return '🟢 High'
                                elif score >= 70:
                                    return '🟡 Medium'
                                else:
                                    return '🔴 Low'
                            for item in alignment_matrix:
                                st.markdown(f"""
<div style='padding:0 0 1.5em 0;'>
  <div style='margin-bottom:0.5em;'>
    <b>Customer Need</b><br>
    <span style='font-size:1.1em'>{item.get('prospect_need', 'N/A')}</span>
  </div>
  <div style='margin-bottom:0.3em;'>
    <b>Our Solution:</b> <span style='color:#1976D2'>{item.get('our_value_component', 'N/A')}</span>
  </div>
  <div style='margin-bottom:0.3em;'>
    <b>Rationale:</b> {item.get('rationale', 'N/A')}
  </div>
  <div style='margin-bottom:0.3em;'>
    <b>Strength:</b> {strength_label(item.get('match_score_percent'))} &nbsp; <b>Confidence:</b> {item.get('match_score_percent', 'N/A')}%
  </div>
  <div style='margin-bottom:0.3em;'>
    <b>Evidence:</b> {item.get('conversation_starter', 'N/A')}
  </div>
</div>
<hr style='border:0;border-top:1px solid #eee;margin:0 0 1.5em 0;'>
""", unsafe_allow_html=True)
                        else:
                            st.markdown(step.get('content', ''))
            else:
                # Step 1: Display Profiler Analysis
                profiler_analysis = playbook_data.get("profiler_analysis")
                if profiler_analysis:
                    with st.expander("Step 1: Company Profile Analysis", expanded=False):
                        st.markdown(f"**Overall Sentiment:** *{profiler_analysis.get('overall_sentiment', 'N/A')}*")
                        st.markdown("**Key Goals Identified:**")
                        for goal in profiler_analysis.get('key_goals', []):
                            st.markdown(f"- {goal}")
                        st.markdown("**Implicit Challenges Identified:**")
                        for challenge in profiler_analysis.get('implicit_challenges', []):
                            st.markdown(f"- {challenge}")
                # Step 2: Display Hypothesizer Analysis
                hypothesizer_analysis = playbook_data.get("hypothesis_analysis")
                if hypothesizer_analysis:
                    with st.expander("Step 2: Hypothesis on Relevant Solutions", expanded=False):
                        st.markdown("**Hypothesis Rationale:**")
                        st.info(f"*{hypothesizer_analysis.get('hypothesis_rationale', 'N/A')}*")
                        st.markdown("**Shortlisted Components for Alignment:**")
                        for item in hypothesizer_analysis.get('shortlist', []):
                            st.markdown(f"- {item}")
                # Step 3: Confirmation of Final Alignment
                if "alignment_matrix" in playbook_data:
                     with st.expander("Step 3: Final Alignment", expanded=False):
                        st.success("The final Value Alignment Matrix was generated based on the analysis above. See the 'Value Alignment' tab for the detailed results.")

        if st.toggle("Show Raw Debug Info"):
            st.subheader("Debug Information")
            st.json(persona)

    if isinstance(persona, dict) and "error" in persona:
        st.error(f"Error generating persona: {persona['error']}")

async def run_persona_tab():
    
    # Clear any invalid demo persona IDs
    selected_persona_id = st.session_state.get("selected_persona_id")
    if selected_persona_id and isinstance(selected_persona_id, str) and selected_persona_id.startswith("demo_"):
        st.session_state.selected_persona_id = None
    
    # If a persona ID is selected, display its details
    selected_persona_id = st.session_state.get("selected_persona_id")
    if selected_persona_id:
        # If user navigated directly to persona generator without coming from search,
        # clear the came_from_search flag
        if not st.session_state.get("came_from_search", False):
            st.session_state["came_from_search"] = False
        
        if not isinstance(selected_persona_id, str):
            st.error("Invalid persona ID")
            return
            
        persona_payload = await get_persona_by_id(selected_persona_id)
        if persona_payload:
            await display_persona_details(persona_payload)
        else:
            st.error("Could not load the selected persona. It may have been deleted.")
            # Check background task for search buttons
            search_background_running, _ = check_background_task_running()
            
            if st.button("Back to Search", key="search_back_to_search",
                        disabled=search_background_running,
                        help="Return to search" if not search_background_running else "Cannot navigate during generation"):
                st.session_state.selected_persona_id = None
                st.rerun()
        return

    # --- This is the generator part ---
    # Check for running background task at the top level - needed for all buttons
    # Use sync version here since we're not in async context at top level
    top_level_background_running, _ = check_background_task_running()
    
    # Create columns for title and buttons on same line
    col_title, col_buttons = st.columns([3, 1])
    
    with col_title:
        st.title("Buyer Persona Generator")
    
    with col_buttons:
        # Show Save and Clear buttons inline with title ONLY when persona is generated
        # But NOT for demo personas
        persona = st.session_state.get("persona")
        is_demo_persona = persona and (
            persona.get("demo_mode", False) or 
            persona.get("demo_customer_name") or 
            persona.get("demo_customer_id")
        )
        
        if persona and not st.session_state.get("selected_persona_id") and not is_demo_persona:
            # Only show Save/Clear buttons for new (not already saved) personas
            if 'persona_saved' not in st.session_state:
                st.session_state.persona_saved = False
            
            # Create compact columns for Save and Clear buttons
            col_save, col_clear = st.columns([1, 1])
            
            with col_save:
                if not st.session_state.persona_saved:
                    # Add custom CSS for both Save and Clear buttons
                    st.markdown("""
                    <style>
                    .stButton > button[kind="primary"] {
                        background-color: #28a745 !important;
                        border-color: #28a745 !important;
                        color: white !important;
                    }
                    .stButton > button[kind="primary"]:hover {
                        background-color: #218838 !important;
                        border-color: #1e7e34 !important;
                    }
                    .stButton > button:has-text("🗑️ Clear Persona") {
                        background-color: #ff8c42 !important;
                        border-color: #ff8c42 !important;
                        color: white !important;
                    }
                    .stButton > button:has-text("🗑️ Clear Persona"):hover {
                        background-color: #e67e22 !important;
                        border-color: #d35400 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    if st.button("💾 Save Persona", key="inline_save_persona", type="primary",
                               disabled=top_level_background_running,
                               help="Save persona to database" if not top_level_background_running else "Cannot save during generation"):
                        with save_spinner(count=0, custom_message="Saving persona..."):  # type: ignore[misc]
                            try:
                                result = await save_persona(persona)  # type: ignore[awaitable]
                                if result:
                                    st.session_state.persona_saved = True
                                    st.toast("✅ Persona saved successfully!", icon="✅")
                                    st.rerun()
                                else:
                                    st.error("Failed to save persona.")
                            except Exception as e:
                                logging.error(f"Exception during persona save: {e}")
                                st.error(f"Exception during save: {e}")
                else:
                    st.button("💾 Saved", disabled=True, key="details_saved_disabled")
            
            with col_clear:
                if st.button("🗑️ Clear Persona", key="inline_clear_persona",
                            disabled=top_level_background_running,
                            help="Clear current persona" if not top_level_background_running else "Cannot clear during generation"):
                    # Show confirmation dialog
                    if st.session_state.get("show_clear_confirmation", False):
                        # User confirmed, proceed with clearing
                        # Clear all persona-related session state
                        if "persona" in st.session_state:
                            del st.session_state["persona"]
                        if "persona_saved" in st.session_state:
                            del st.session_state["persona_saved"]
                        if "generated_persona" in st.session_state:
                            del st.session_state["generated_persona"]
                        if "generator_version" in st.session_state:
                            del st.session_state["generator_version"]
                        if "generation_success_time" in st.session_state:
                            del st.session_state["generation_success_time"]
                        
                        # Clear the website input
                        st.session_state.clear_input_on_next_run = True
                        
                        # Reset confirmation state
                        st.session_state.show_clear_confirmation = False
                        
                        st.toast("🗑️ Persona cleared successfully!", icon="🗑️")
                        st.rerun()
                    else:
                        # Show confirmation dialog
                        st.session_state.show_clear_confirmation = True
                        st.rerun()
        else:
            pass  # No additional buttons needed for new personas
    
    # --- State management for clearing input ---
    if "clear_input_on_next_run" not in st.session_state:
        st.session_state.clear_input_on_next_run = False
    if st.session_state.clear_input_on_next_run:
        st.session_state.website_input = ""
        st.session_state.clear_input_on_next_run = False
    
    # --- Initialize session state for persona generation ---
    if "persona_in_progress" not in st.session_state:
        st.session_state.persona_in_progress = False
    if "generation_step" not in st.session_state:
        st.session_state.generation_step = ""
    if "generated_persona" not in st.session_state:
        st.session_state.generated_persona = None
    if "generator_version" not in st.session_state:
        st.session_state.generator_version = None
    if "generation_success_time" not in st.session_state:
        st.session_state.generation_success_time = 0
    if "persona" not in st.session_state:
        st.session_state.persona = None
    if "background_persona_task_id" not in st.session_state:
        st.session_state.background_persona_task_id = None

    # --- Value Components Validation ---
    def check_value_components_completion():
        """Check if at least 90% of value components are filled."""
        try:
            from app.categories import COMPONENT_STRUCTURES
            from app.database import fetch_all_value_components
            
            # Get user's value components using demo profile manager
            from app.components.demo_companies.demo_profile_manager import demo_profile_manager
            user_id = demo_profile_manager.get_current_user_id()
            demo_mode = st.session_state.get("user_demo_mode", False)
            
            # Force refresh by clearing cache and fetching fresh data
            st.cache_data.clear()
            user_components = fetch_all_value_components(user_id=user_id)
            
            # Debug logging
            logging.warning(f"[persona_tab.py] Checking completion - user_id={user_id}, demo_mode={demo_mode}")
            logging.warning(f"[persona_tab.py] Session state user_id={st.session_state.get('user_id', 'NOT_SET')}")
            logging.warning(f"[persona_tab.py] User components type: {type(user_components)}")
            if isinstance(user_components, dict):
                logging.warning(f"[persona_tab.py] User components keys: {list(user_components.keys())}")
                for main_cat, components_list in user_components.items():
                    if isinstance(components_list, list):
                        logging.warning(f"[persona_tab.py] {main_cat}: {len(components_list)} components")
                        # Log sample component for debugging
                        if len(components_list) > 0:
                            sample = components_list[0]
                            logging.warning(f"[persona_tab.py] Sample component from {main_cat}: category='{sample.get('category')}', name='{sample.get('name')}', has_original={bool(sample.get('original_value'))}, has_ai={bool(sample.get('ai_processed_value'))}")
            elif isinstance(user_components, list):
                logging.warning(f"[persona_tab.py] User components is list with {len(user_components)} items")
            else:
                logging.warning(f"[persona_tab.py] User components is empty or unexpected type: {user_components}")
            
            # Count total available fields
            total_fields = 0
            filled_fields = 0
            
            for main_cat, main_details in COMPONENT_STRUCTURES.items():
                for sub_cat, sub_details in main_details["subcategories"].items():
                    for item in sub_details["items"]:
                        total_fields += 1
                        
                        # Check if this field is filled
                        field_name = item["name"]
                        field_filled = False
                        
                        # Check in user's components - NEW FORMAT: {"main_category": [{"category": "...", "name": "...", ...}, ...]}
                        if isinstance(user_components, dict):
                            main_cat_lc = main_cat.lower()
                            sub_cat_lc = sub_cat.lower()
                            field_name_lc = field_name.lower()
                            
                            # Look for the component in the list format
                            if main_cat_lc in user_components and isinstance(user_components[main_cat_lc], list):
                                for comp in user_components[main_cat_lc]:
                                    if isinstance(comp, dict):
                                        comp_category = comp.get("category", "").lower()
                                        comp_name = comp.get("name", "").lower()
                                        
                                        # Debug: Log first few comparisons to see what's happening
                                        if filled_fields < 3 or not field_filled:
                                            logging.warning(f"[persona_tab.py] Comparing: looking_for='{main_cat_lc}/{sub_cat_lc}/{field_name_lc}' vs found='{comp_category}/{comp_name}'")
                                        
                                        if comp_category == sub_cat_lc and comp_name == field_name_lc:
                                            # Check if either original_value or ai_processed_value is filled
                                            original_val = comp.get("original_value", "").strip()
                                            ai_val = comp.get("ai_processed_value", "").strip()
                                            
                                            if original_val or ai_val:
                                                field_filled = True
                                                filled_fields += 1  # Increment the counter!
                                                logging.warning(f"[persona_tab.py] ✓ Found filled field: {main_cat}/{sub_cat}/{field_name} = '{original_val[:50]}...' or '{ai_val[:50]}...' (filled_fields now: {filled_fields})")
                                                break
            
            completion_percentage = (filled_fields / total_fields) * 100 if total_fields > 0 else 0
            
            # Additional debug if no data found
            if isinstance(user_components, dict) and len(user_components) == 0:
                logging.warning(f"[persona_tab.py] ⚠️ NO DATA FOUND for user_id={user_id}! This might be why completion is 0%.")
                logging.warning(f"[persona_tab.py] Check if data was saved with this user_id. Session state user_id={st.session_state.get('user_id', 'NOT_SET')}")
            elif isinstance(user_components, dict) and len(user_components) > 0:
                total_components_in_db = sum(len(v) if isinstance(v, list) else 1 for v in user_components.values())
                logging.warning(f"[persona_tab.py] Found {total_components_in_db} total components in DB across {len(user_components)} categories")
            
            logging.warning(f"[persona_tab.py] Completion check result: {filled_fields}/{total_fields} = {completion_percentage:.1f}%")
            
            # Additional debug: Show which fields are missing
            if completion_percentage < 90:
                missing_fields = []
                for main_cat, main_details in COMPONENT_STRUCTURES.items():
                    for sub_cat, sub_details in main_details["subcategories"].items():
                        for item in sub_details["items"]:
                            field_name = item["name"]
                            field_filled = False
                            
                            if isinstance(user_components, dict):
                                main_cat_lc = main_cat.lower()
                                sub_cat_lc = sub_cat.lower()
                                field_name_lc = field_name.lower()
                                
                                if main_cat_lc in user_components and isinstance(user_components[main_cat_lc], list):
                                    for comp in user_components[main_cat_lc]:
                                        if isinstance(comp, dict):
                                            comp_category = comp.get("category", "").lower()
                                            comp_name = comp.get("name", "").lower()
                                            
                                            if comp_category == sub_cat_lc and comp_name == field_name_lc:
                                                original_val = comp.get("original_value", "").strip()
                                                ai_val = comp.get("ai_processed_value", "").strip()
                                                
                                                if original_val or ai_val:
                                                    field_filled = True
                                                    break
                            
                            if not field_filled:
                                missing_fields.append(f"{main_cat}/{sub_cat}/{field_name}")
                
                logging.warning(f"[persona_tab.py] Missing fields: {missing_fields[:10]}...")  # Show first 10 missing fields
            
            return completion_percentage
        except Exception as e:
            logging.error(f"Error checking value components completion: {e}")
            return 0
    
    completion_percentage = check_value_components_completion()
    min_required_percentage = 90
    
    # Debug: Show completion details
    if completion_percentage < min_required_percentage:
        st.info(f"🔍 **Debug Info:** Value components completion is {completion_percentage:.1f}% (need {min_required_percentage}%). Check the logs for details.")

    # --- Only show generation UI when no persona exists ---
    
    if not st.session_state.get("persona"):
        # Check if demo mode is active from sidebar
        user_demo_mode = st.session_state.get("user_demo_mode", False)
        
        if user_demo_mode:
            # --- Demo Customer Selector ---
            demo_integration = DemoIntegration()
            selected_demo_customer = demo_integration.render_demo_customer_selector()
            
            if selected_demo_customer:
                # Always use demo:// format for demo customers
                website = f"demo://{selected_demo_customer.get('id', 'unknown')}"
            else:
                website = None
            
            # Add separator line before generate button
            st.markdown("---")
            
            # Show generate button for demo mode (also check for background tasks)
            # Use centralized helper function
            demo_background_running, _ = check_background_task_running()
            demo_generate_disabled = demo_background_running
            
            if demo_background_running:
                st.error("⏳ Another persona generation is already in progress. Please wait for completion.")
            
            generate_clicked = st.button("Generate Buyer Persona", key="demo_generate_button", disabled=demo_generate_disabled, type="primary")
        else:
            # --- Website Input and Validation ---
            # Check if user has ANY running background task (only one per user at a time)
            # CRITICAL: Check session state FIRST - this is the fastest and most reliable indicator
            task_id_in_session = st.session_state.get("background_persona_task_id")
            
            # Use columns to make input field 30% width
            col1, col2 = st.columns([3, 7])  # 30% width for input, 70% empty space
            
            with col1:
                # Disable URL input if background task is running or completed (until user views persona)
                # Check task status to determine if input should be disabled
                url_disabled = False
                url_value = ""  # Default empty value
                
                if task_id_in_session:
                    try:
                        from app.database import get_background_task
                        task_check = await get_background_task(task_id_in_session)
                        if task_check:
                            task_status_check = task_check.get("status")
                            # Disable if running (generation in progress) or completed (waiting for user to view)
                            if task_status_check in ["running", "completed"]:
                                url_disabled = True
                                # Get the website URL from the task to show in the input field
                                url_value = task_check.get("website", "")
                    except Exception:
                        # If we can't check, assume running if task_id exists
                        url_disabled = True
                
                # When disabled, show the URL from the task instead of placeholder
                # When enabled, let Streamlit manage the value via the key
                website_input = st.text_input(
                    "Enter company website URL:", 
                    value=url_value if url_disabled and url_value else None,  # Only set value when disabled and we have a URL from task
                    placeholder="https://example.com",
                    key="website_input_field",
                    disabled=url_disabled,
                    help="URL input is disabled while persona generation is in progress" if url_disabled else None
                )
                # Strip whitespace from URL input
                website = website_input.strip() if website_input else ""
            
            # Initialize variables for task status tracking
            running_task_website = None
            task_status = None
            background_task_running = False
            
            if task_id_in_session:
                # We have a task_id - check if task is actually running or completed
                
                # Try to get task details from DB to check status
                try:
                    from app.database import get_background_task
                    task_details = await get_background_task(task_id_in_session)
                    
                    if task_details:
                        task_status = task_details.get("status")
                        running_task_website = task_details.get("website", "unknown")
                        
                        # CRITICAL: If task is completed or failed, show completion/failure message on main page
                        if task_status in ["completed", "failed"]:
                            if task_status == "completed":
                                st.session_state[f"cached_progress_{task_id_in_session}"] = {
                                    "progress_percent": 100,
                                    "current_step": "✅ Completed",
                                    "status": "completed"
                                }
                                
                                # Show completion message with prominent View Persona button
                                result_persona = task_details.get("result_persona")
                                if result_persona:
                                    # Extract persona_id from result - try multiple paths
                                    persona_id = None
                                    if isinstance(result_persona, dict):
                                        # Try multiple extraction paths
                                        # Path 1: Top-level ID
                                        persona_id = result_persona.get("id")
                                        
                                        # Path 2: Company.id
                                        if not persona_id:
                                            company_dict = result_persona.get("company")
                                            if isinstance(company_dict, dict):
                                                persona_id = company_dict.get("id")
                                        
                                        # Path 3: Nested persona dict (if result_persona is payload structure)
                                        if not persona_id and "persona" in result_persona:
                                            nested_persona = result_persona.get("persona")
                                            if isinstance(nested_persona, dict):
                                                persona_id = nested_persona.get("id")
                                                if not persona_id and isinstance(nested_persona.get("company"), dict):
                                                    persona_id = nested_persona["company"].get("id")
                                        
                                        # Log for debugging if ID still not found
                                        if not persona_id:
                                            logger.debug(f"[persona_tab] Persona ID extraction failed. result_persona keys: {list(result_persona.keys())}, has company: {isinstance(result_persona.get('company'), dict)}, has persona: {'persona' in result_persona}")
                                        
                                        # If still no ID, try to find persona by website as fallback
                                        if not persona_id and running_task_website:
                                            try:
                                                from app.database import get_personas
                                                # Search for persona by website
                                                all_personas = await get_personas()
                                                # Find the most recent persona for this website
                                                # Note: get_personas returns point.payload which has {"id": "...", "persona": {...}, "source_website": "..."}
                                                matching_personas = [
                                                    p for p in all_personas 
                                                    if isinstance(p, dict) and 
                                                    p.get("source_website") == running_task_website
                                                ]
                                                if matching_personas:
                                                    # Sort by created_at (most recent first)
                                                    matching_personas.sort(
                                                        key=lambda x: x.get("created_at", "") or x.get("scan_date", ""), 
                                                        reverse=True
                                                    )
                                                    # Get ID from the most recent matching persona
                                                    most_recent = matching_personas[0]
                                                    persona_id = most_recent.get("id")
                                                    if persona_id:
                                                        logger.info(f"[persona_tab] Found persona ID {persona_id} by website lookup for {running_task_website}")
                                            except Exception as e:
                                                logger.debug(f"[persona_tab] Could not search for persona by website: {e}")
                                    
                                    # CRITICAL: Check if persona has rejection/error status even if task is "completed"
                                    persona_status = None
                                    persona_error = None
                                    if isinstance(result_persona, dict):
                                        persona_status = result_persona.get("status")
                                        persona_error = result_persona.get("error")
                                        # Also check nested persona dict
                                        if not persona_status and "persona" in result_persona:
                                            nested_persona = result_persona.get("persona")
                                            if isinstance(nested_persona, dict):
                                                persona_status = nested_persona.get("status")
                                                persona_error = nested_persona.get("error")
                                    
                                    # Check if this is a rejection persona (rejected_for_relevance, rejected_company_mismatch, etc.)
                                    is_rejection = (
                                        persona_status and 
                                        ("rejected" in str(persona_status).lower() or "rejection" in str(persona_status).lower())
                                    ) or (
                                        persona_error and 
                                        ("not relevant" in str(persona_error).lower() or 
                                         "rejected" in str(persona_error).lower() or
                                         "mismatch" in str(persona_error).lower())
                                    )
                                    
                                    if is_rejection:
                                        # Show rejection message instead of success
                                        if f"rejection_toast_shown_{task_id_in_session}" not in st.session_state:
                                            st.toast("⚠️ Website rejected by quality checks", icon="⚠️")
                                            st.session_state[f"rejection_toast_shown_{task_id_in_session}"] = True
                                        
                                        st.markdown("---")
                                        st.error(f"❌ **Persona generation rejected:** {persona_error or 'Quality gate check failed'}")
                                        
                                        # Show rejection details if available
                                        if isinstance(result_persona, dict):
                                            rejection_details = result_persona.get("relevance_validation") or result_persona.get("validation_details")
                                            if rejection_details:
                                                with st.expander("📋 View rejection details", expanded=False):
                                                    if isinstance(rejection_details, dict):
                                                        if "why_not_relevant" in rejection_details:
                                                            st.write(f"**Reason:** {rejection_details.get('why_not_relevant')}")
                                                        if "relevance_score" in rejection_details:
                                                            st.write(f"**Relevance Score:** {rejection_details.get('relevance_score', 0)}/10")
                                                        st.json(rejection_details)
                                                    else:
                                                        st.write(str(rejection_details))
                                        
                                        st.info("💡 **What to do:** Try a different website URL that is more relevant to your business, or check your Value Components configuration.")
                                        
                                        # Option to view the rejection persona anyway (for debugging)
                                        if persona_id:
                                            if st.button("👁️ View Rejection Details", key=f"view_rejection_{task_id_in_session}", use_container_width=True):
                                                st.session_state.selected_persona_id = persona_id
                                                st.session_state["current_page"] = "Persona Generator"
                                                st.session_state.background_persona_task_id = None
                                                if f"rejection_toast_shown_{task_id_in_session}" in st.session_state:
                                                    del st.session_state[f"rejection_toast_shown_{task_id_in_session}"]
                                                st.rerun()
                                        
                                        st.markdown("---")
                                    elif persona_id:
                                        # Normal success case
                                        # Show toast notification (only once)
                                        if f"completion_toast_shown_{task_id_in_session}" not in st.session_state:
                                            st.toast("🎉 Persona generation completed successfully!", icon="✅")
                                            st.session_state[f"completion_toast_shown_{task_id_in_session}"] = True
                                        
                                        # Show prominent success message with View Persona button
                                        st.markdown("---")
                                        st.success("🎉 **Persona generation completed successfully!**")
                                        
                                        # Prominent View Persona button
                                        if st.button("👁️ View Generated Persona", key=f"view_persona_main_{task_id_in_session}", type="primary", use_container_width=True):
                                            st.session_state.selected_persona_id = persona_id
                                            st.session_state["current_page"] = "Persona Generator"
                                            st.session_state.background_persona_task_id = None
                                            # Clear completion toast flag
                                            if f"completion_toast_shown_{task_id_in_session}" in st.session_state:
                                                del st.session_state[f"completion_toast_shown_{task_id_in_session}"]
                                            st.rerun()
                                        
                                        st.markdown("---")
                                    else:
                                        # ID not found - log for debugging and show helpful message
                                        logger.warning(f"[persona_tab] Persona ID not found in result_persona. Keys: {list(result_persona.keys()) if isinstance(result_persona, dict) else 'not a dict'}, Website: {running_task_website}")
                                        st.warning("⚠️ Persona generation completed but persona ID not found.")
                                        st.info("💡 You can find your persona in the **Persona Search** tab using the website URL.")
                                        # Still show a button to navigate to Persona Search
                                        if st.button("🔍 Go to Persona Search", key=f"goto_search_{task_id_in_session}", use_container_width=True):
                                            st.session_state["current_page"] = "Persona Search"
                                            st.rerun()
                            elif task_status == "failed":
                                error_message = task_details.get("error_message", "Unknown error")
                                st.markdown("---")
                                st.error(f"❌ **Persona generation failed:** {error_message}")
                                st.info("💡 You can try again with a different URL or check your Value Components.")
                                st.markdown("---")
                                # Clear task_id for failed tasks
                                st.session_state.background_persona_task_id = None
                            
                            # For completed tasks, keep task_id until user views persona or starts new generation
                            # This ensures the completion button persists across reruns
                            background_task_running = False
                            
                            logger.info(f"Task {task_id_in_session} is {task_status}, background_task_running={background_task_running}")
                        elif task_status == "running":
                            background_task_running = True
                        else:
                            # Unknown status - assume running to be safe
                            background_task_running = True
                    else:
                        # Task not found in DB - might be timing issue, assume running based on session state
                        background_task_running = True
                        
                except Exception as e:
                    logger.debug(f"Could not get task details from DB: {e}, using session state")
                    # If we can't check, assume running based on session state
                    background_task_running = True
                    
                # Fallback: If we couldn't get task details, check for any running task
                if task_status is None:
                    try:
                        from app.database import get_any_running_task_for_user
                        user_id = st.session_state.get('user_id', 'anonymous')
                        existing_task = await get_any_running_task_for_user(user_id)
                        if existing_task:
                            running_task_website = existing_task.get("website", "unknown")
                            # Ensure task_id is set (should already be, but be safe)
                            task_id = existing_task.get("task_id")
                            if task_id and task_id != task_id_in_session:
                                st.session_state.background_persona_task_id = task_id
                            background_task_running = True
                    except Exception as e:
                        logger.debug(f"Could not get running task details: {e}, using session state")
                        background_task_running = True
            else:
                # No task_id in session - check database
                try:
                    from app.database import get_any_running_task_for_user
                    user_id = st.session_state.get('user_id', 'anonymous')
                    existing_task = await get_any_running_task_for_user(user_id)
                    
                    if existing_task:
                        background_task_running = True
                        running_task_website = existing_task.get("website", "unknown")
                        # CRITICAL: Ensure task_id is set for sidebar progress
                        task_id = existing_task.get("task_id")
                        if task_id:
                            st.session_state.background_persona_task_id = task_id
                    else:
                        background_task_running = False
                        running_task_website = None
                except Exception as e:
                    logger.debug(f"Could not check database for running task: {e}")
                    background_task_running = False
                    running_task_website = None
            
            # CRITICAL: Show progress indicator on main page (not sidebar)
            # This replaces the sidebar progress display
            if background_task_running and (task_status is None or task_status != "completed"):
                # Render progress display on main page
                task_id_for_progress = task_id_in_session or st.session_state.get("background_persona_task_id")
                if task_id_for_progress:
                    try:
                        from app.database import get_background_task
                        progress_task = await get_background_task(task_id_for_progress)
                        
                        if progress_task:
                            progress_percent = progress_task.get("progress_percent", 0)
                            current_step = progress_task.get("current_step", "Initializing...")
                            progress_task_status = progress_task.get("status", "running")
                            result_persona = progress_task.get("result_persona")
                            # Get website from progress_task for fallback lookup
                            progress_task_website = progress_task.get("website") or running_task_website
                            
                            # CRITICAL FALLBACK: Check if task is effectively complete even if status is still "running"
                            # This handles cases where the status update is delayed
                            is_effectively_complete = (
                                progress_percent >= 100 and
                                (
                                    "Completed" in current_step or
                                    "Quality Assurance" in current_step or
                                    result_persona is not None
                                )
                            )
                            
                            # If effectively complete, show completion message instead of progress
                            # NOTE: result_persona might not be set yet, so we'll try to find persona by website
                            if is_effectively_complete:
                                # Treat as completed - show completion message
                                logger.info(f"[persona_tab] Task {task_id_for_progress} is effectively complete (100% progress, step: {current_step}), attempting to show completion message")
                                
                                # Extract persona_id using same logic as completion handler
                                persona_id = None
                                
                                # First, try to get ID from result_persona if it exists
                                if result_persona and isinstance(result_persona, dict):
                                    persona_id = (
                                        result_persona.get("id") or
                                        (result_persona.get("company", {}) or {}).get("id") if isinstance(result_persona.get("company"), dict) else None
                                    )
                                    
                                    # Try nested persona dict
                                    if not persona_id and "persona" in result_persona:
                                        nested_persona = result_persona.get("persona")
                                        if isinstance(nested_persona, dict):
                                            persona_id = nested_persona.get("id")
                                            if not persona_id and isinstance(nested_persona.get("company"), dict):
                                                persona_id = nested_persona["company"].get("id")
                                
                                # CRITICAL: If no result_persona or no ID found, try lookup by website
                                # This handles cases where task is complete but result_persona hasn't been saved yet
                                if not persona_id and progress_task_website:
                                    try:
                                        from app.database import get_personas
                                        all_personas = await get_personas()
                                        matching_personas = [
                                            p for p in all_personas 
                                            if isinstance(p, dict) and 
                                            p.get("source_website") == progress_task_website
                                        ]
                                        if matching_personas:
                                            matching_personas.sort(
                                                key=lambda x: x.get("created_at", "") or x.get("scan_date", ""), 
                                                reverse=True
                                            )
                                            most_recent = matching_personas[0]
                                            persona_id = most_recent.get("id")
                                            if persona_id:
                                                logger.info(f"[persona_tab] Found persona ID {persona_id} by website lookup for {progress_task_website}")
                                    except Exception as e:
                                        logger.debug(f"[persona_tab] Could not search for persona by website: {e}")
                                
                                # CRITICAL: Check if persona has rejection/error status even if task is effectively complete
                                persona_status = None
                                persona_error = None
                                if result_persona and isinstance(result_persona, dict):
                                    persona_status = result_persona.get("status")
                                    persona_error = result_persona.get("error")
                                    # Also check nested persona dict
                                    if not persona_status and "persona" in result_persona:
                                        nested_persona = result_persona.get("persona")
                                        if isinstance(nested_persona, dict):
                                            persona_status = nested_persona.get("status")
                                            persona_error = nested_persona.get("error")
                                
                                # Check if this is a rejection persona
                                is_rejection = (
                                    persona_status and 
                                    ("rejected" in str(persona_status).lower() or "rejection" in str(persona_status).lower())
                                ) or (
                                    persona_error and 
                                    ("not relevant" in str(persona_error).lower() or 
                                     "rejected" in str(persona_error).lower() or
                                     "mismatch" in str(persona_error).lower())
                                )
                                
                                if is_rejection:
                                    # Show rejection message
                                    if f"rejection_toast_shown_{task_id_for_progress}" not in st.session_state:
                                        st.toast("⚠️ Website rejected by quality checks", icon="⚠️")
                                        st.session_state[f"rejection_toast_shown_{task_id_for_progress}"] = True
                                    
                                    st.markdown("---")
                                    st.error(f"❌ **Persona generation rejected:** {persona_error or 'Quality gate check failed'}")
                                    
                                    # Show rejection details if available
                                    if result_persona and isinstance(result_persona, dict):
                                        rejection_details = result_persona.get("relevance_validation") or result_persona.get("validation_details")
                                        if rejection_details:
                                            with st.expander("📋 View rejection details", expanded=False):
                                                if isinstance(rejection_details, dict):
                                                    if "why_not_relevant" in rejection_details:
                                                        st.write(f"**Reason:** {rejection_details.get('why_not_relevant')}")
                                                    if "relevance_score" in rejection_details:
                                                        st.write(f"**Relevance Score:** {rejection_details.get('relevance_score', 0)}/10")
                                                    st.json(rejection_details)
                                                else:
                                                    st.write(str(rejection_details))
                                    
                                    st.info("💡 **What to do:** Try a different website URL that is more relevant to your business, or check your Value Components configuration.")
                                    
                                    # Option to view the rejection persona anyway
                                    if persona_id:
                                        if st.button("👁️ View Rejection Details", key=f"view_rejection_{task_id_for_progress}", use_container_width=True):
                                            st.session_state.selected_persona_id = persona_id
                                            st.session_state["current_page"] = "Persona Generator"
                                            st.session_state.background_persona_task_id = None
                                            if f"rejection_toast_shown_{task_id_for_progress}" in st.session_state:
                                                del st.session_state[f"rejection_toast_shown_{task_id_for_progress}"]
                                            st.rerun()
                                    
                                    st.markdown("---")
                                elif persona_id:
                                    # Normal success case
                                    # Show completion message
                                    if f"completion_toast_shown_{task_id_for_progress}" not in st.session_state:
                                        st.toast("🎉 Persona generation completed successfully!", icon="✅")
                                        st.session_state[f"completion_toast_shown_{task_id_for_progress}"] = True
                                    
                                    st.markdown("---")
                                    st.success("🎉 **Persona generation completed successfully!**")
                                    
                                    if st.button("👁️ View Generated Persona", key=f"view_persona_main_{task_id_for_progress}", type="primary", use_container_width=True):
                                        st.session_state.selected_persona_id = persona_id
                                        st.session_state["current_page"] = "Persona Generator"
                                        st.session_state.background_persona_task_id = None
                                        if f"completion_toast_shown_{task_id_for_progress}" in st.session_state:
                                            del st.session_state[f"completion_toast_shown_{task_id_for_progress}"]
                                        st.rerun()
                                    
                                    st.markdown("---")
                                    # Skip the progress display - don't render it below
                                else:
                                    # Effectively complete but no persona_id - show progress with warning
                                    st.markdown("---")
                                    with st.container():
                                        st.info(f"🔄 **Generating persona...**")
                                        st.progress(progress_percent / 100)
                                        col_step, col_percent = st.columns([3, 1])
                                        with col_step:
                                            st.caption(f"**Step:** {current_step}")
                                        with col_percent:
                                            st.caption(f"**Progress:** {progress_percent}%")
                                        st.warning("⚠️ Generation appears complete but persona ID not found. Please check Persona Search tab.")
                                        if st.button("🔄 Refresh Progress", key=f"refresh_progress_main_{task_id_for_progress}", help="Manually refresh progress"):
                                            st.rerun()
                                    st.markdown("---")
                            else:
                                # Not effectively complete - show normal progress
                                st.markdown("---")
                                with st.container():
                                    st.info(f"🔄 **Generating persona...**")
                                    
                                    # Progress bar
                                    st.progress(progress_percent / 100)
                                    
                                    # Step and percentage info
                                    col_step, col_percent = st.columns([3, 1])
                                    with col_step:
                                        st.caption(f"**Step:** {current_step}")
                                    with col_percent:
                                        st.caption(f"**Progress:** {progress_percent}%")
                                    
                                    # Manual refresh button
                                    if st.button("🔄 Refresh Progress", key=f"refresh_progress_main_{task_id_for_progress}", help="Manually refresh progress"):
                                        st.rerun()
                                    
                                    # Auto-refresh every 3 seconds if task is running
                                    import time
                                    if progress_task_status == "running":
                                        current_time = time.time()
                                        last_auto_refresh = st.session_state.get(f"last_progress_refresh_{task_id_for_progress}", 0)
                                        if current_time - last_auto_refresh > 3:
                                            st.session_state[f"last_progress_refresh_{task_id_for_progress}"] = current_time
                                            st.rerun()
                                
                                st.markdown("---")
                        else:
                            # Task not found yet - show initializing state
                            st.markdown("---")
                            st.info("🔄 Persona generation in progress...")
                            st.markdown("---")
                    except Exception as e:
                        logger.debug(f"Could not get progress task: {e}")
                        # Show fallback message
                        st.markdown("---")
                        st.info("🔄 Persona generation in progress...")
                        st.markdown("---")
        
            # --- Simple completion check ---
            if completion_percentage < min_required_percentage:
                # Show toasts only once when user first visits with incomplete components
                if "value_components_toast_shown" not in st.session_state:
                    st.toast("Please complete your Value Components first before generating personas.", icon="⚠️")
                    st.toast("Go to 'Value Components' in the sidebar to fill in your company's value propositions.", icon="💡")
                    st.session_state.value_components_toast_shown = True
                
                st.markdown("---")
            else:
                # Reset the flag when components are complete
                if "value_components_toast_shown" in st.session_state:
                    del st.session_state.value_components_toast_shown
            
            # Disable button if processing, invalid URL, insufficient value components, or background task running
            is_processing = st.session_state.get("persona_in_progress", False)
            
            # Check if we're in demo mode (user choice overrides global config)
            from app.config import ENABLE_DEMO_MODE
            from app.database import fetch_all_value_components
            
            # User can override demo mode via checkbox
            user_demo_mode = st.session_state.get("user_demo_mode", False)
            global_demo_mode = ENABLE_DEMO_MODE
            
            # Demo mode is active if either user chooses it OR global config enables it
            demo_mode_active = user_demo_mode or global_demo_mode
            
            # ALWAYS enforce value components completion - no bypasses in demo mode
            # This ensures proper data quality and user engagement even in demo scenarios
            has_sufficient_components = completion_percentage >= min_required_percentage
            is_valid_url = utils.is_valid_url(website)
            
            # Debug logging for URL validation issues
            if website and not is_valid_url:
                logger.debug(f"URL validation failed for: '{website}' (type: {type(website)}, length: {len(website) if website else 0})")
            
            # Show demo mode indicator but emphasize that value components are still required
            if demo_mode_active:
                if user_demo_mode and not st.session_state.get("user_demo_toast_shown", False):
                    st.toast("🎭 **User Demo Mode** - Value components still required for quality personas", icon="🎭")
                    st.session_state.user_demo_toast_shown = True
                elif not user_demo_mode and not st.session_state.get("global_demo_toast_shown", False):
                    st.toast("🎭 **Global Demo Mode** - Value components still required for quality personas", icon="🎭")
                    st.session_state.global_demo_toast_shown = True
            
            # Include background task check in disable condition
            # Also check processing flag
            is_processing_flag = st.session_state.get("persona_in_progress", False)
            generate_disabled = (is_processing or is_processing_flag or not is_valid_url or not has_sufficient_components or 
                               background_task_running)
            
            # Generate button with simple status - show only ONE message with priority order
            # BUT: Don't show error if task is completed (completion message is shown above)
            # NOTE: Reduced duplicate warnings - sidebar shows progress, so keep main area minimal
            if generate_disabled and (task_status is None or task_status != "completed"):
                # Priority 1: Background task running - but don't duplicate sidebar message
                if background_task_running:
                    # Don't show error here - sidebar already shows progress
                    # Just disable the button (which is already done)
                    pass
                # Priority 2: Invalid URL
                elif not is_valid_url:
                    st.error("❌ Please enter a valid website URL")
                # Priority 3: Insufficient value components
                elif not has_sufficient_components:
                    # Use same column layout as URL input for consistent width
                    col1, col2 = st.columns([3, 7])
                    with col1:
                        st.error(f"❌ Complete Value Components first ({completion_percentage:.1f}% complete, need 90%)")
                    with col2:
                        if st.button("🔄 Refresh Check", help="Refresh the completion check"):
                            st.rerun()
                # Priority 4: Processing flag set (shouldn't happen if background_task_running is correct, but as fallback)
                elif is_processing:
                    st.info("⏳ Persona generation in progress...")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                generate_clicked = st.button("Generate Buyer Persona", disabled=generate_disabled, type="primary")
            with col2:
                # Clear Tasks button - always active, stops execution and resets
                clear_disabled = False  # Always enabled
                if st.button("🔄 Clear Tasks", key="clear_tasks_button", disabled=clear_disabled, help="Stop current generation and reset to ready state"):
                    # Get current task_id before clearing
                    current_task_id = st.session_state.get("background_persona_task_id")
                    
                    # Cancel task in database if running
                    if current_task_id:
                        try:
                            from app.database import get_background_task, update_background_task
                            task_to_cancel = await get_background_task(current_task_id)
                            if task_to_cancel and task_to_cancel.get("status") == "running":
                                await update_background_task(current_task_id, status="cancelled")
                                logger.info(f"[persona_tab] Cancelled task {current_task_id}")
                        except Exception as e:
                            logger.debug(f"Could not cancel task in database: {e}")
                    
                    # Clear all task-related session state
                    st.session_state.background_persona_task_id = None
                    st.session_state.persona_in_progress = False
                    
                    # Clear all progress-related placeholders
                    if current_task_id:
                        placeholder_keys = [
                            f"progress_info_{current_task_id}",
                            f"progress_bar_{current_task_id}",
                            f"progress_step_{current_task_id}",
                            f"progress_percent_{current_task_id}",
                            f"progress_rendered_{current_task_id}",
                            f"completion_shown_{current_task_id}",
                            f"completion_toast_shown_{current_task_id}",
                            f"cached_progress_{current_task_id}"
                        ]
                        for key in placeholder_keys:
                            if key in st.session_state:
                                del st.session_state[key]
                    
                    st.toast("🔄 Tasks cleared. Ready for new generation.", icon="🔄")
                    st.rerun()

        # Handle button click OR post-verification generation
        # Check if we should proceed after verification
        should_proceed_after_verification = st.session_state.get("pending_generation_after_verification", False)
        
        # CRITICAL: Check if verification is in progress - if so, DO NOT proceed with generation
        # Import here to avoid circular dependency
        from app.utils.domain_company_lookup import get_domain_from_url as get_domain
        domain_for_check = get_domain(website) if website else ""
        verification_in_progress = st.session_state.get(f"verification_in_progress_{domain_for_check}", False) if domain_for_check else False
        
        # CRITICAL: If verification is in progress, show modal and STOP - do not proceed with generation
        if verification_in_progress and not should_proceed_after_verification:
            # Verification is in progress but user hasn't confirmed yet
            # Show the modal and wait - do NOT enter generation block
            if not website or not isinstance(website, str):
                # No website URL available - cannot show verification modal
                logger.warning("[persona_tab] Verification in progress but no website URL available")
                return
            from app.components.company_verification import render_company_verification_modal
            # Type narrowing: website is guaranteed to be str at this point
            verified_data = await render_company_verification_modal(website, pid=0)
            if verified_data is None:
                # Still waiting for user action
                return
            # User confirmed - clear flag and proceed below
            if f"verification_in_progress_{domain_for_check}" in st.session_state:
                del st.session_state[f"verification_in_progress_{domain_for_check}"]
            st.session_state.pending_generation_after_verification = True
            st.rerun()
            return
        
        # Only proceed if button clicked OR verification completed, AND verification is NOT in progress
        if (generate_clicked or should_proceed_after_verification) and not verification_in_progress:
            try:
                # Additional safety check - if already processing, don't proceed
                if st.session_state.get("persona_in_progress", False):
                    st.warning("⚠️ Persona generation already in progress. Please wait.")
                    return
                
                # CRITICAL: Set processing flag IMMEDIATELY to prevent double-clicks
                st.session_state.persona_in_progress = True
                
                # Clear pending generation flag if we're proceeding
                if should_proceed_after_verification:
                    st.session_state.pending_generation_after_verification = False
                
                # Step 1: Company Verification (Required for non-demo mode)
                if website and not website.startswith("demo://"):
                    from app.components.company_verification import render_company_verification_modal, get_verified_company
                    from app.utils.domain_company_lookup import get_domain_from_url
                    
                    domain = get_domain_from_url(website)
                    verified_company = get_verified_company(domain)
                    
                    # If not verified, show verification modal and stop here (wait for user)
                    if not verified_company or not verified_company.get("verified", False):
                        # Check if verification is in progress (prevents auto-generation on reruns)
                        verification_in_progress = st.session_state.get(f"verification_in_progress_{domain}", False)
                        
                        # Show verification modal if:
                        # 1. Button was clicked (initial trigger)
                        # 2. Verification is in progress (user is in the middle of verification)
                        should_show_modal = generate_clicked or verification_in_progress
                        
                        if should_show_modal:
                            # Show verification modal (await since it's now async)
                            verified_data = await render_company_verification_modal(website, pid=0)
                            
                            if verified_data is None:
                                # User cancelled or hasn't confirmed yet - stop here and wait
                                # CRITICAL: Do NOT proceed with generation
                                # Keep persona_in_progress True so modal stays visible on rerun
                                # Keep verification_in_progress True so we know to show modal again
                                logger.info(f"[persona_tab] Verification modal returned None - stopping and waiting for user action")
                                # Keep persona_in_progress True to prevent other actions, but don't start generation
                                # The verification_in_progress flag is already set by the modal
                                return
                            
                            # User confirmed - store verified company
                            st.session_state.verified_company_name = verified_data.get("company_name")
                            st.session_state.verified_industry = verified_data.get("industry")
                            st.session_state.verified_company_data = verified_data
                            
                            # CRITICAL: Clear verification_in_progress BEFORE setting pending flag
                            # This ensures generation can proceed
                            if f"verification_in_progress_{domain}" in st.session_state:
                                del st.session_state[f"verification_in_progress_{domain}"]
                            
                            # Set flag to proceed with generation on next rerun
                            st.session_state.pending_generation_after_verification = True
                            st.rerun()
                            return
                        else:
                            # Should not happen - if not verified and not from button click, something is wrong
                            st.error("Company verification required. Please click 'Generate Buyer Persona' first.")
                            st.session_state.persona_in_progress = False
                            return
                    else:
                        # Use cached verification
                        st.session_state.verified_company_name = verified_company.get("company_name")
                        st.session_state.verified_industry = verified_company.get("industry")
                        st.session_state.verified_company_data = verified_company
                
                # Check if this is demo mode
                if website and website.startswith("demo://"):
                    # For demo mode, keep the demo:// URL and pass demo customer context
                    # Extract demo customer ID
                    demo_customer_id = website.replace("demo://", "")
                    
                    # Get demo customer info
                    demo_customers = st.session_state.get("demo_customers", [])
                    demo_customer = None
                    for customer in demo_customers:
                        if customer.get("id") == demo_customer_id:
                            demo_customer = customer
                            break
                    
                    # Set demo mode flag in session state
                    st.session_state.demo_mode_active = True
                    st.session_state.demo_progress = 0
                    st.session_state.demo_current_step = "Initializing..."
                    
                    # Use demo-specific persona generation (keep demo:// URL)
                    from app.ai.personas import build_buyer_persona
                    demo_persona = await build_buyer_persona(website, None, 0, None)  # type: ignore[arg-type]
                    
                    # Clear processing flag
                    st.session_state.persona_in_progress = False
                    
                    if "error" in demo_persona:
                        st.error(f"❌ Demo generation failed: {demo_persona['error']}")
                    else:
                        st.success("✅ Demo persona generated successfully!")
                        st.session_state.demo_mode_active = False
                        st.session_state.demo_progress = 100
                        st.session_state.demo_current_step = "Completed"
                        
                        # Store the demo persona in session state for display
                        st.session_state.persona = demo_persona
                        # Don't set selected_persona_id for demo personas since they're not in the database
                        
                        # Add a small delay to let toasts be visible before rerun
                        import time
                        time.sleep(0.5)
                    st.rerun()
                else:
                    # Normal mode - use background tasks with website-specific checking
                    if not website or not utils.is_valid_url(website):
                        st.error("❌ Please enter a valid website URL")
                        st.session_state.persona_in_progress = False
                        return
                    
                    from app.database import check_and_create_background_task
                    from app.ai.personas import run_persona_generation_background
                    
                    # Get user ID
                    user_id = st.session_state.get('user_id', 'anonymous')
                    
                    # CRITICAL: Before creating new task, check if there's a completed task and clear it
                    # This allows users to start new generation without clicking "Clear Tasks"
                    existing_task_id = st.session_state.get("background_persona_task_id")
                    if existing_task_id:
                        try:
                            from app.database import get_background_task
                            existing_task = await get_background_task(existing_task_id)
                            if existing_task and existing_task.get("status") in ["completed", "failed"]:
                                # Clear completed/failed task to allow new generation
                                logger.info(f"[persona_tab] Auto-clearing completed task {existing_task_id} to allow new generation")
                                st.session_state.background_persona_task_id = None
                                # Clear container key if it exists
                                container_key = f"progress_container_{existing_task_id}"
                                if container_key in st.session_state:
                                    del st.session_state[container_key]
                        except Exception as e:
                            logger.debug(f"Could not check existing task status: {e}")
                    
                    # Check if task already exists for this website and create if needed
                    task_id, status, message = await check_and_create_background_task(user_id, website)
                    
                    if status == "already_running":
                        # Task already running for user (any website)
                        # Set the existing task ID in session state
                        from app.database import get_any_running_task_for_user
                        existing_task = await get_any_running_task_for_user(user_id)
                        if existing_task:
                            st.session_state.background_persona_task_id = existing_task.get("task_id")
                        
                        # Clear processing flag
                        st.session_state.persona_in_progress = False
                        st.rerun()
                        return
                    elif status == "error":
                        # Error creating task
                        st.error(f"❌ {message}")
                        st.session_state.persona_in_progress = False
                        return
                    elif status == "created":
                        # New task created successfully
                        # CRITICAL: Store task ID in session state IMMEDIATELY
                        # This must happen before rerun so sidebar can see it
                        st.session_state.background_persona_task_id = task_id
                        logger.info(f"[persona_tab] Task {task_id} created, stored in session state")
                        
                        # Reset failed task flag for new task
                        if "failed_task_shown" in st.session_state:
                            del st.session_state.failed_task_shown
                        
                        # Clear processing flag (task is running in background)
                        st.session_state.persona_in_progress = False
                        
                        # Get verified company data
                        verified_company_name = st.session_state.get("verified_company_name")
                        verified_industry = st.session_state.get("verified_industry")
                        
                        # Start background generation (non-blocking)
                        import threading
                        def run_background_task():
                            import asyncio
                            try:
                                if task_id:
                                    asyncio.run(run_persona_generation_background(
                                        task_id, 
                                        website, 
                                        user_id,
                                        verified_company_name=verified_company_name,
                                        verified_industry=verified_industry
                                    ))
                            except Exception as e:
                                logger.error(f"[Background Thread] Error in persona generation: {e}", exc_info=True)
                        
                        # Start the background task in a separate thread
                        background_thread = threading.Thread(target=run_background_task, daemon=True)
                        background_thread.start()
                        logger.info(f"[persona_tab] Background thread started for task {task_id}")
                        
                        # Show success message - progress will be shown on main page
                        st.success("🚀 Persona generation started! Progress will be shown below.")
                        
                        # CRITICAL: Ensure task_id is visible to sidebar immediately
                        # The sidebar checks session state FIRST, so this should work
                        logger.info(f"[persona_tab] Task {task_id} stored in session state, rerunning page...")
                        
                        # IMPORTANT: Force a small delay to ensure task is in database before rerun
                        # This ensures sidebar can find the task
                        import time
                        time.sleep(0.1)
                        
                        # Verify task_id is still in session state before rerun
                        if st.session_state.get("background_persona_task_id") != task_id:
                            logger.warning(f"[persona_tab] Task ID mismatch! Expected {task_id}, got {st.session_state.get('background_persona_task_id')}")
                            st.session_state.background_persona_task_id = task_id
                        
                        # Allow user to navigate away
                        st.rerun()
                
            except Exception as e:
                logging.error(f"Exception starting background persona generation: {e}")
                st.error(f"Failed to start persona generation: {e}")
                # Clear processing flag on error
                st.session_state.persona_in_progress = False

    # --- Display generated persona and actions ---
    if st.session_state.get("persona"):
        persona = st.session_state["persona"]

        # --- Display Temporary Success Message on Generation ---
        if st.session_state.get('generation_success_time', 0) > 0 and \
           time.time() - st.session_state.generation_success_time < 3:
            st.toast("✅ Buyer persona generated successfully!", icon="✅")
            # Reset the timer so it doesn't show again on rerun
            st.session_state.generation_success_time = 0


        if isinstance(persona, dict) and "error" in persona:
            if "company" in persona:
                # This is a fallback persona, show a warning but display it
                st.warning(f"⚠️ Persona generated with limitations: {persona['error']}")
                await display_persona_details(persona)
            else:
                # This is a pure error, show error message
                st.error(f"Error generating persona: {persona['error']}")
        else:
            # The save button is now inside display_persona_details
            await display_persona_details(persona)

async def persona_tab():
    await run_persona_tab() 