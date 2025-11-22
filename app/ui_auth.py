"""
Main UI with Authentication
Integrates authentication system with the existing UI.
"""

import streamlit as st
import logging
import asyncio
import time
import os
from datetime import datetime
from typing import Optional
# Remove auth imports from top level to avoid database connection during import
# Remove all imports from top level to avoid database connection during import

logger = logging.getLogger(__name__)

class AuthenticatedUI:
    """Main UI class with authentication integration."""
    
    def __init__(self):
        # Lazy load all components to avoid connecting during import
        self.user_manager = None
        self.session_manager = None
        self.user_db = None
    
    def _initialize_auth_components(self):
        """Initialize auth components when needed."""
        if self.user_manager is None:
            # Import UserManager and SessionManager only when needed
            from .auth.user_management import UserManager
            from .auth.session_manager import SessionManager
            # Create UserManager without client initially
            self.user_manager = UserManager()
            self.session_manager = SessionManager(self.user_manager)
    
    def initialize_user_database(self, user_id: str):
        """Initialize user-aware database for the current user."""
        from .database_user import UserAwareDatabase
        self.user_db = UserAwareDatabase(user_id)
    
    def render_sidebar(self):
        """Render the sidebar with navigation and user info."""
        # Initialize auth components if needed
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            self._initialize_auth_components()
        
        # Ensure session_manager is initialized
        if self.session_manager is None:
            return
        
        # Try to restore session on page load
        if not self.session_manager.is_authenticated():
            self.session_manager.restore_session()
        
        # Check authentication status
        has_session = "user_id" in st.session_state and st.session_state.user_id is not None
        is_trying_auth = (st.session_state.get("login_submitted", False) or 
                         st.session_state.get("register_submitted", False))
        
        if has_session or is_trying_auth:
            is_authenticated = self.session_manager.is_authenticated()
        else:
            is_authenticated = False
        
        with st.sidebar:
            st.markdown("## 🎢 Value Rollercoaster")
            
            
            # Show user info if authenticated
            if is_authenticated and self.session_manager is not None:
                from .auth.ui_components import render_user_header
                render_user_header(self.session_manager)
                
                # Background task progress indicator - REMOVED from sidebar
                # Progress is now shown on the main Persona Generator page for better UX
                # self.render_background_task_progress()  # Disabled - progress moved to main page
                
                # Navigation - match original app exactly
                st.markdown("---")
                
                # Check if user wants to see settings
                if st.session_state.get("show_user_settings", False):
                    from .auth.ui_components import render_user_settings
                    render_user_settings(self.session_manager)
                    return
                
                # Main navigation - use buttons like original app
                SIDEBAR_MENU = [
                    {"label": "Value Components", "icon": "💎"},
                    {"label": "Persona Generator", "icon": "👤"},
                    {"label": "Persona Search", "icon": "🔍"},
                    {"label": "API Chart", "icon": "📊"},
                ]
                
                nav_labels = [item["label"] for item in SIDEBAR_MENU]
                nav_icons = [item["icon"] for item in SIDEBAR_MENU]
                
                # Check if we should override navigation due to persona selection FIRST
                if st.session_state.get("selected_persona_id"):
                    st.session_state["current_page"] = "Persona Generator"
                
                # Check if background task is running - disable navigation during generation
                # Use centralized helper function for consistency
                try:
                    from app.components.persona_tab import check_background_task_running
                    nav_background_running, _ = check_background_task_running()
                except Exception as e:
                    # Fallback to session state check
                    nav_background_running = st.session_state.get("background_persona_task_id") is not None
                    logger.debug(f"Could not check background task for navigation: {e}")
                
                # Track which button is clicked in this run
                selected_nav = st.session_state.get("current_page", nav_labels[0])
                for label, icon in zip(nav_labels, nav_icons):
                    nav_disabled = nav_background_running
                    nav_help = f"Navigate to {label}" if not nav_disabled else "Cannot navigate during persona generation"
                    
                    if st.button(f"{icon}  {label}", use_container_width=True, 
                                key=f"nav_btn_{label}", 
                                disabled=nav_disabled,
                                help=nav_help):
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
                            # Lazy load categories to avoid import delays
                            try:
                                from app.categories import COMPONENT_STRUCTURES
                                main_category_labels = ["Summary"] + list(COMPONENT_STRUCTURES.keys())
                                main_category_icons = ["🧮"] + [COMPONENT_STRUCTURES[cat]["icon"] for cat in COMPONENT_STRUCTURES.keys()]
                                menu_options = [f"{icon} {cat}" for icon, cat in zip(main_category_icons, main_category_labels)]
                            except ImportError as e:
                                logger.error(f"Error importing categories: {e}")
                                # Fallback to basic categories
                                main_category_labels = ["Summary", "Technical Value", "Business Value", "Strategic Value", "After Sales Value"]
                                main_category_icons = ["🧮", "🛠️", "💰", "🎯", "🤝"]
                                menu_options = [f"{icon} {cat}" for icon, cat in zip(main_category_icons, main_category_labels)]
                            
                            # Initialize session state if not exists (like original app)
                            if "main_tab_radio" not in st.session_state:
                                st.session_state["main_tab_radio"] = 0
                            if "selected_main_category" not in st.session_state:
                                st.session_state["selected_main_category"] = main_category_labels[0]
                            
                            # --- Category selection using dropdown (like original app) ---
                            reset_key = st.session_state.get("selectbox_reset_key", 0)
                            selected_category = st.selectbox(
                                "Value Category",
                                options=main_category_labels,
                                index=0,
                                key=f"category_selectbox_{reset_key}"
                            )
                            
                            # Find the index of the selected category
                            selected_idx = main_category_labels.index(selected_category)
                            
                            # Always update session state
                            st.session_state["main_tab_radio"] = selected_idx
                            st.session_state["selected_main_category"] = selected_category
                            st.session_state["main_tab_selectbox"] = selected_idx
                            
                            # Add separation line after the dropdown
                            st.markdown("---")
                
                # User statistics (lazy load)
                if self.user_db and st.session_state.get("current_page") == "Value Components":
                    try:
                        stats = self.user_db.get_user_statistics()
                        if not isinstance(stats, dict) or "error" not in stats:
                            st.markdown("### 📊 Your Data")
                            st.metric("Value Components", stats.get("value_components", 0))
                            st.metric("Personas", stats.get("personas", 0))
                            st.metric("Analyses", stats.get("analyses", 0))
                            st.metric("Website Structures", stats.get("website_structures", 0))
                    except Exception as e:
                        logger.error(f"Error loading user statistics: {e}")
                        # Continue without statistics
                
                # Admin tools (only for default user - admin)
                if self.session_manager is not None and self.session_manager.get_username() == "default_user":
                    st.markdown("---")
                    st.markdown("### 🔧 Admin Tools")
                    
                    # Row 1: Persona Management
                    if st.button("👥 Persona Management", help="Manage persona collection", use_container_width=True):
                        st.session_state.current_page = "Persona Management"
                        st.rerun()
                    
                    # Row 2: User Management
                    if st.button("👤 User Management", help="Manage user accounts and activity", use_container_width=True):
                        st.session_state.current_page = "User Management"
                        st.rerun()
                    
                    # Row 3: Password Management
                    if st.button("🔐 Password Management", help="Reset user passwords", use_container_width=True):
                        st.session_state.current_page = "Password Management"
                        st.rerun()
                    
                    # Row 4: Company Profile Management
                    if st.button("🏢 Company Profile", help="Manage company profile and settings", use_container_width=True):
                        st.session_state.current_page = "Company Profile"
                        st.rerun()
                    
                    # Row 5: Company Website Management
                    if st.button("🌐 Company Website", help="Manage website scraping and content extraction", use_container_width=True):
                        st.session_state.current_page = "Company Website"
                        st.rerun()
                    
                    # Row 6: AI Framework (Admin Debug View)
                    if st.button("🤖 AI Framework", help="View industry framework generation and usage", use_container_width=True):
                        st.session_state.current_page = "AI Framework"
                        st.rerun()
                    
                
                # Help button (like original app)
                st.markdown("---")
                from app.components.help_modal import render_help_button
                render_help_button()
    
    def render_background_task_progress(self):
        """Show background task progress in sidebar."""
        try:
            # Check for user demo mode first
            user_demo_mode = st.session_state.get("user_demo_mode", False)
            if user_demo_mode:
                st.info("🎭 **User Demo Mode Active**")
                return
            
            # Check for demo mode first
            if st.session_state.get("demo_mode_active", False):
                st.info(f"🎭 Demo Mode Active")
                progress = st.session_state.get("demo_progress", 0)
                current_step = st.session_state.get("demo_current_step", "Initializing...")
                st.progress(progress / 100)
                st.caption(f"Step: {current_step}")
                st.caption(f"Progress: {progress}%")
                return
            
            # Check for background task
            from app.database import get_background_task, get_any_running_task_for_user
            
            task_id = st.session_state.get("background_persona_task_id")
            
            # CRITICAL: If we have task_id in session state, show progress immediately
            # Don't wait for database query - session state is authoritative
            if task_id:
                # We have task_id - show progress even if we can't query DB yet
                # This ensures progress shows immediately on rerun after task creation
                pass  # Continue to show progress below
            else:
                # No task_id in session - try to find one in database
                try:
                    import asyncio
                    user_id = st.session_state.get('user_id', 'anonymous')
                    # Try to get running task for user
                    try:
                        loop = asyncio.get_running_loop()
                        # We're in async context - can't use asyncio.run()
                        # Try using the helper function instead
                        try:
                            from app.components.persona_tab import check_background_task_running
                            has_task, _ = check_background_task_running()
                            if has_task:
                                task_id = st.session_state.get("background_persona_task_id")
                                if not task_id:
                                    return  # Helper couldn't set it either
                            else:
                                return
                        except Exception:
                            return
                    except RuntimeError:
                        # No running loop - safe to use asyncio.run()
                        existing_task = asyncio.run(get_any_running_task_for_user(user_id))
                        if existing_task:
                            task_id = existing_task.get("task_id")
                            if task_id:
                                st.session_state.background_persona_task_id = task_id
                        else:
                            return
                except Exception as e:
                    logger.debug(f"Could not check for running task in sidebar: {e}")
                    return
            
            # If we still don't have task_id, try one more time to restore from database
            if not task_id:
                # Last attempt: check database for any running task for this user
                try:
                    import asyncio
                    user_id = st.session_state.get('user_id', 'anonymous')
                    try:
                        loop = asyncio.get_running_loop()
                        # In async context - can't query, but try the helper
                        from app.components.persona_tab import check_background_task_running
                        has_task, _ = check_background_task_running()
                        if has_task:
                            task_id = st.session_state.get("background_persona_task_id")
                    except RuntimeError:
                        # Safe to query
                        existing_task = asyncio.run(get_any_running_task_for_user(user_id))
                        if existing_task:
                            task_id = existing_task.get("task_id")
                            if task_id:
                                st.session_state.background_persona_task_id = task_id
                except Exception as e:
                    logger.debug(f"Final attempt to restore task_id failed: {e}")
                
                # If still no task_id, can't show progress
                if not task_id:
                    return
            
            # Now get task details
            import asyncio
            task = None
            
            # CRITICAL: If we have task_id, show progress even if we can't query DB
            # This handles async context and timing issues
            cached_progress = st.session_state.get(f"cached_progress_{task_id}", {})
            
            # CRITICAL: Show progress ONCE - check cached progress first (fastest path)
            if cached_progress:
                cached_status = cached_progress.get("status", "running")
                
                # Check if task is completed in cache
                if cached_status == "completed":
                    # CRITICAL: Keep task_id until user views persona - don't clear it here
                    # This ensures the completion button persists
                    st.success("✅ **Persona ready!**")
                    st.caption("Generation completed successfully")
                    st.caption("💡 Check the main tab to view your persona")
                    
                    # Try to get task from DB to show View Persona button
                    try:
                        try:
                            loop = asyncio.get_running_loop()
                            # In async context - can't query, show message only
                            st.info("💡 Click 'View Persona' in the main tab to see your generated persona")
                            return
                        except RuntimeError:
                            # Safe to query
                            task = asyncio.run(get_background_task(task_id))
                            if task and task.get("result_persona"):
                                result_persona = task.get("result_persona")
                                persona_id = None
                                if isinstance(result_persona, dict):
                                    persona_id = result_persona.get("id")
                                    if not persona_id and isinstance(result_persona.get("company"), dict):
                                        persona_id = result_persona["company"].get("id")
                                
                                if persona_id:
                                    if st.button("👁️ View Persona", key="view_background_persona_cached", type="primary"):
                                        st.session_state.selected_persona_id = persona_id
                                        st.session_state["current_page"] = "Persona Generator"
                                        st.session_state.background_persona_task_id = None
                                        st.rerun()
                                else:
                                    st.info("💡 Click 'View Persona' in the main tab to see your generated persona")
                            else:
                                st.info("💡 Click 'View Persona' in the main tab to see your generated persona")
                    except Exception:
                        st.info("💡 Click 'View Persona' in the main tab to see your generated persona")
                    return
                else:
                    # Show cached progress (ONLY ONCE)
                    st.info("🔄 Generating persona...")
                    st.progress(cached_progress.get("progress_percent", 0) / 100)
                    st.caption(f"Step: {cached_progress.get('current_step', 'In progress...')}")
                    st.caption(f"Progress: {cached_progress.get('progress_percent', 0)}%")
                    
                    # Try to get latest data from DB if possible, but don't show progress again
                    try:
                        # Check if we're in async context
                        try:
                            loop = asyncio.get_running_loop()
                            # In async context - can't use asyncio.run()
                            # We already showed progress above, so just return
                            return
                        except RuntimeError:
                            # No running loop - safe to use asyncio.run()
                            task = asyncio.run(get_background_task(task_id))
                            if task:
                                # Update cache with latest data (but don't show progress again)
                                st.session_state[f"cached_progress_{task_id}"] = {
                                    "progress_percent": task.get("progress_percent", 0),
                                    "current_step": task.get("current_step", "In progress..."),
                                    "status": task.get("status", "running")
                                }
                                
                                # If completed, update cache and show completion
                                # NOTE: We don't auto-rerun here to prevent button re-enabling
                                # User must manually refresh to see completion status
                                if task.get("status") == "completed":
                                    # Update cache with completion status
                                    st.session_state[f"cached_progress_{task_id}"] = {
                                        "progress_percent": 100,
                                        "current_step": "✅ Completed",
                                        "status": "completed"
                                    }
                                    # Don't clear task_id - keep it so completion message persists
                                    # Don't auto-rerun - let user manually refresh to see completion
                                    return
                    except Exception:
                        pass  # Already showed progress, ignore errors
                    
                    # Manual refresh button only (NO auto-refresh to prevent button re-enabling)
                    if st.button("🔄 Refresh Progress", key="manual_progress_refresh", help="Manually refresh progress"):
                        # CRITICAL: Clear cache to force fresh data fetch
                        preserved_task_id = st.session_state.get("background_persona_task_id")
                        if preserved_task_id:
                            # Clear the cached progress to force fresh fetch
                            cache_key = f"cached_progress_{preserved_task_id}"
                            if cache_key in st.session_state:
                                del st.session_state[cache_key]
                        # Force rerun to check fresh status from database
                        st.rerun()
                    
                    return  # CRITICAL: Return after showing progress to prevent duplicates
            else:
                # No cache - try to get task from DB immediately and show progress
                try:
                    # Check if we're in async context
                    try:
                        loop = asyncio.get_running_loop()
                        # In async context - can't use asyncio.run()
                        # Show basic progress and return
                        st.info("🔄 Generating persona...")
                        st.progress(0.1)  # Show minimal progress bar
                        st.caption("Initializing...")
                        st.caption("Progress updating...")
                        return
                    except RuntimeError:
                        # No running loop - safe to use asyncio.run()
                        task = asyncio.run(get_background_task(task_id))
                        if task:
                            # Update cache for next time
                            task_status = task.get("status", "running")
                            st.session_state[f"cached_progress_{task_id}"] = {
                                "progress_percent": task.get("progress_percent", 0),
                                "current_step": task.get("current_step", "In progress..."),
                                "status": task_status
                            }
                            
                            # If completed, show completion with View Persona button
                            if task_status == "completed":
                                st.session_state[f"cached_progress_{task_id}"] = {
                                    "progress_percent": 100,
                                    "current_step": "✅ Completed",
                                    "status": "completed"
                                }
                                st.success("✅ **Persona ready!**")
                                st.caption("Generation completed successfully")
                                
                                # Try to get persona_id and show View Persona button
                                result_persona = task.get("result_persona")
                                persona_id = None
                                if result_persona and isinstance(result_persona, dict):
                                    persona_id = result_persona.get("id")
                                    if not persona_id and isinstance(result_persona.get("company"), dict):
                                        persona_id = result_persona["company"].get("id")
                                
                                if persona_id:
                                    if st.button("👁️ View Persona", key="view_background_persona_no_cache", type="primary", use_container_width=True):
                                        st.session_state.selected_persona_id = persona_id
                                        st.session_state["current_page"] = "Persona Generator"
                                        st.session_state.background_persona_task_id = None
                                        # Clear cache
                                        cache_key = f"cached_progress_{task_id}"
                                        if cache_key in st.session_state:
                                            del st.session_state[cache_key]
                                        st.rerun()
                                else:
                                    st.caption("💡 Check the main tab to view your persona")
                                return
                            
                            # Show actual progress from database
                            st.info("🔄 Generating persona...")
                            st.progress(task["progress_percent"] / 100)
                            st.caption(f"Step: {task['current_step']}")
                            st.caption(f"Progress: {task['progress_percent']}%")
                            
                            # Add refresh button for running tasks
                            if st.button("🔄 Refresh Progress", key="manual_progress_refresh_no_cache", help="Manually refresh progress"):
                                # Clear cache to force fresh fetch
                                cache_key = f"cached_progress_{task_id}"
                                if cache_key in st.session_state:
                                    del st.session_state[cache_key]
                                st.rerun()
                        else:
                            # Task not found - show basic progress
                            st.info("🔄 Generating persona...")
                            st.progress(0.1)  # Show minimal progress bar
                            st.caption("Initializing...")
                            st.caption("Progress updating...")
                            
                            # Update cache with basic progress
                            st.session_state[f"cached_progress_{task_id}"] = {
                                "progress_percent": 0,
                                "current_step": "Initializing...",
                                "status": "running"
                            }
                            
                            # Add refresh button for tasks not found
                            if st.button("🔄 Refresh Progress", key="manual_progress_refresh_not_found", help="Manually refresh progress"):
                                # Clear cache to force fresh fetch
                                cache_key = f"cached_progress_{task_id}"
                                if cache_key in st.session_state:
                                    del st.session_state[cache_key]
                                st.rerun()
                except Exception as e:
                    logger.warning(f"Error getting task details in sidebar: {e}")
                    # Show basic progress as fallback
                    st.info("🔄 Generating persona...")
                    st.progress(0.1)
                    st.caption("Initializing...")
                    st.caption("Progress updating...")
                    
                    # Manual refresh button only (NO auto-refresh to prevent button re-enabling)
                    if st.button("🔄 Refresh Progress", key="manual_progress_refresh_error", help="Manually refresh progress"):
                        preserved_task_id = st.session_state.get("background_persona_task_id")
                        if preserved_task_id:
                            cache_key = f"cached_progress_{preserved_task_id}"
                            if cache_key in st.session_state:
                                del st.session_state[cache_key]
                        st.rerun()
                    return
            
            # If we got here, we have task from DB - show it (but only if we haven't already)
            # This should only happen if we didn't have cached_progress and successfully got task from DB
            if task and task.get("status") == "running":
                # Update cache for future async context fallbacks
                st.session_state[f"cached_progress_{task_id}"] = {
                    "progress_percent": task.get("progress_percent", 0),
                    "current_step": task.get("current_step", "In progress..."),
                    "status": "running"
                }
                
                st.info("🔄 Generating persona...")
                st.progress(task["progress_percent"] / 100)
                st.caption(f"Step: {task['current_step']}")
                st.caption(f"Progress: {task['progress_percent']}%")
                
                # Manual refresh button only (NO auto-refresh to prevent button re-enabling)
                if st.button("🔄 Refresh Progress", key="manual_progress_refresh_final", help="Manually refresh progress"):
                    # CRITICAL: Clear cache to force fresh data fetch
                    preserved_task_id = st.session_state.get("background_persona_task_id")
                    if preserved_task_id:
                        # Clear the cached progress to force fresh fetch
                        cache_key = f"cached_progress_{preserved_task_id}"
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                    st.rerun()
                
            elif task and task.get("status") == "completed":
                # Update cache with completion status
                st.session_state[f"cached_progress_{task_id}"] = {
                    "progress_percent": 100,
                    "current_step": "✅ Completed",
                    "status": "completed"
                }
                
                # CRITICAL: Keep task_id until user views persona - don't clear it here
                # This ensures the completion button persists across reruns
                
                # Check if this is a recently completed task that was restored
                if st.session_state.get("recently_completed_task", False):
                    st.success("🎉 Persona completed while you were away!")
                    st.caption("Your persona generation finished successfully.")
                    # Clear the flag
                    st.session_state.recently_completed_task = False
                else:
                    st.success("✅ Persona ready!")
                    st.caption("Generation completed successfully")
                    
                if st.button("👁️ View Persona", key="view_background_persona", type="primary"):
                    # Navigate to persona results
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
                            st.session_state.selected_persona_id = persona_id
                            st.session_state["current_page"] = "Persona Generator"
                            st.session_state.background_persona_task_id = None  # Clear task only after viewing
                            st.rerun()
                        else:
                            st.error("Persona ID not found in result data")
                    else:
                        st.error("Persona data not available")
                        
            elif task and task.get("status") == "failed":
                st.error(f"❌ Generation failed")
                st.caption(f"Error: {task.get('error_message', 'Unknown error')}")
                if st.button("Clear", key="clear_failed_task"):
                    st.session_state.background_persona_task_id = None
                    st.rerun()
                
                # Auto-refresh once for failed tasks to show error immediately
                if not st.session_state.get("failed_task_shown"):
                    st.session_state.failed_task_shown = True
                    st.rerun()
                    
        except Exception as e:
            import logging
            logging.error(f"Error rendering background task progress: {e}")
            st.error("Error loading task progress")
    
    def render_main_content(self):
        """Render the main content area."""
        # Initialize auth components if needed
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            self._initialize_auth_components()
        
        # Ensure session_manager is initialized
        if self.session_manager is None:
            return
        
        # Try to restore session on page load
        if not self.session_manager.is_authenticated():
            self.session_manager.restore_session()
        
        # Check if user is authenticated
        is_authenticated = self.session_manager.is_authenticated()
        
        # Check for authentication-related actions
        has_session = "user_id" in st.session_state and st.session_state.user_id is not None
        is_trying_auth = (st.session_state.get("login_submitted", False) or 
                         st.session_state.get("register_submitted", False))
        needs_auth_check = (st.session_state.get("show_register", False) or 
                           st.session_state.get("show_user_settings", False))
        
        if not is_authenticated:
            # Show a simple login page without database connection
            self.render_simple_auth_page()
            return
        
        # Get user ID for later use
        if self.session_manager is None:
            return
        user_id = self.session_manager.get_user_id()
        
        if user_id is None:
            st.error("User ID not available")
            return
        
        # --- Initialize database collections if not already done ---
        if not st.session_state.get("collections_initialized", False):
            try:
                with st.spinner("Initializing database..."):
                    from app.database import ensure_collections_exist
                    result = asyncio.run(ensure_collections_exist())
                    if result:
                        st.session_state["collections_initialized"] = True
                        logger.info("Database collections initialized successfully")
                    else:
                        st.error("Failed to initialize database collections")
                        return
            except Exception as e:
                st.error(f"Error initializing database: {e}")
                logger.error(f"Error initializing database: {e}")
                return
        
        
        
        
        # Check for admin pages based on current_page
        current_page = st.session_state.get("current_page", "Value Components")
        
        if current_page == "Persona Management":
            self.render_persona_management_ui()
            return
        
        if current_page == "User Management":
            self.render_user_management_ui()
            return
        
        if current_page == "Password Management":
            self.render_password_management_ui()
            return
        
        if current_page == "Company Profile":
            self.render_company_profile_ui()
            return
        
        if current_page == "Company Website":
            self.render_company_website_ui()
            return
        
        if current_page == "AI Framework":
            self.render_ai_framework_ui()
            return
        
        
        
        
        # Show main UI
        current_page = st.session_state.get("current_page", "Value Components")
        
        # Only initialize database if user is on Value Components page
        if current_page == "Value Components":
            # Initialize user database only when needed
            if not self.user_db or self.user_db.user_id != user_id:
                self.initialize_user_database(user_id)
        
        # Pass user database to main UI
        try:
            # Import and call the main UI function lazily
            from app.ui import show_main_ui
            asyncio.run(show_main_ui(current_page, user_db=self.user_db if current_page == "Value Components" else None))
        except Exception as e:
            st.error(f"Error loading main UI: {e}")
            logger.error(f"Error in main UI: {e}")

    
    def on_auth_success(self):
        """Callback when authentication is successful."""
        st.rerun()
    
    def render_simple_auth_page(self):
        """Render a simple authentication page without database connection."""
        # Center the content using columns
        col_left, col_center, col_right = st.columns([35, 30, 35])
        
        with col_center:
            st.markdown("# 🎢 Value Rollercoaster")
            
            # Check if user wants to register
            show_register = st.session_state.get("show_register", False)
            
            if show_register:
                self.render_simple_register_form()
            else:
                self.render_simple_login_form()
            
            # Add some helpful information
            st.markdown("---")
            st.markdown("### 💡 Tips:")
            #st.markdown("- Use the default account: `default_user` / `default`")
            st.markdown("- Create your own account to keep your data separate")
            st.markdown("- Your data is private and isolated from other users")
    
    def render_simple_login_form(self):
        """Render a simple login form without database connection."""
        
        with st.form("simple_login_form"):
            st.markdown("### 🔐 Login")
            st.markdown("---")
            
            username = st.text_input("Username", key="simple_login_username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="simple_login_password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me", value=True)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                login_submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            with col2:
                register_clicked = st.form_submit_button("Register New User", use_container_width=True)
            
            if login_submitted and username and password:
                # Initialize auth components only when user tries to log in
                if not hasattr(self, 'session_manager') or self.session_manager is None:
                    self._initialize_auth_components()
                
                if self.session_manager is not None and self.session_manager.login_user(username, password):
                    st.success(f"Welcome back, {username}!")
                    self.on_auth_success()
                else:
                    st.error("Invalid username or password.")
            
            if register_clicked:
                st.session_state.show_register = True
                st.rerun()
    
    def render_simple_register_form(self):
        """Render a simple registration form without database connection."""
        
        with st.form("simple_register_form"):
            st.markdown("### 📝 Create New Account")
            st.markdown("---")
            
            username = st.text_input("Username", key="simple_register_username", placeholder="Choose a username")
            display_name = st.text_input("Display Name", key="simple_register_display_name", placeholder="Your display name (optional)")
            password = st.text_input("Password", type="password", key="simple_register_password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="simple_register_confirm_password", placeholder="Confirm your password")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                register_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
            
            with col2:
                back_to_login = st.form_submit_button("Back to Login", use_container_width=True)
            
            if back_to_login:
                st.session_state.show_register = False
                st.rerun()
            
            if register_submitted:
                if not username or not password:
                    st.error("Username and password are required.")
                    return
                
                if password != confirm_password:
                    st.error("Passwords do not match.")
                    return
                
                if len(password) < 3:
                    st.error("Password must be at least 3 characters long.")
                    return
                
                # Initialize auth components only when user tries to register
                if not hasattr(self, 'session_manager') or self.session_manager is None:
                    self._initialize_auth_components()
                
                try:
                    if self.session_manager is not None and self.session_manager.create_user_and_login(username, password, display_name):
                        st.success(f"Account created successfully! Welcome, {username}!")
                        self.on_auth_success()
                    else:
                        st.error("Failed to create account. Username might already exist.")
                except Exception as e:
                    st.error(f"Error creating account: {str(e)}")
    
    def render_persona_management_ui(self):
        """Render the persona management UI for admin users."""
        st.markdown("# 👥 Persona Collection Management")
        st.markdown("---")
        
        st.markdown("""
        ### Persona Collection Overview
        
        This tool allows you to manage the personas collection:
        - **View all personas** with details
        - **Delete individual personas** by ID
        - **Delete all personas** (nuclear option)
        - **Export persona data** for backup
        """)
        
        # Current persona statistics
        st.markdown("### 📊 Current Persona Statistics")
        try:
            from app.database import QDRANT_CLIENT, PERSONA_COLLECTION
            from app.database import ensure_persona_collection
            
            # Ensure collection exists
            ensure_persona_collection()
            
            # Get collection info
            info = QDRANT_CLIENT.get_collection(PERSONA_COLLECTION)
            st.metric("Total Personas", info.points_count)
            st.metric("Total Vectors", info.vectors_count)
            
            # Get sample personas
            if info.points_count > 0:
                st.markdown("### 👤 Sample Personas")
                results, _ = QDRANT_CLIENT.scroll(
                    collection_name=PERSONA_COLLECTION,
                    limit=5,
                    with_payload=True,
                    with_vectors=False
                )
                
                for i, point in enumerate(results):
                    payload = point.payload
                    persona = payload.get("persona", {})
                    company = persona.get("company", {})
                    
                    with st.expander(f"👤 {company.get('name', 'Unknown Company')} (ID: {point.id})"):
                        st.markdown(f"**Industry**: {persona.get('industry', 'Unknown')}")
                        st.markdown(f"**Created**: {payload.get('created_at', 'Unknown')}")
                        st.markdown(f"**Source**: {payload.get('source_website', 'Unknown')}")
                        
                        # Delete individual persona
                        if st.button(f"🗑️ Delete This Persona", key=f"delete_{point.id}"):
                            try:
                                from app.database import delete_persona_by_id
                                import asyncio
                                result = asyncio.run(delete_persona_by_id(point.id))
                                if result:
                                    st.success("✅ Persona deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete persona")
                            except Exception as e:
                                st.error(f"❌ Error deleting persona: {e}")
            
        except Exception as e:
            st.error(f"❌ Error checking persona status: {e}")
        
        # Bulk operations
        st.markdown("### 🔧 Bulk Operations")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("📥 Export All Personas", help="Export persona data as JSON"):
                try:
                    with st.spinner("Exporting personas..."):
                        from app.database import get_personas
                        import asyncio
                        import json
                        from datetime import datetime
                        
                        personas = asyncio.run(get_personas())
                        if personas:
                            # Create export data
                            export_data = {
                                "export_date": datetime.now().isoformat(),
                                "total_personas": len(personas),
                                "personas": personas
                            }
                            
                            # Create download button
                            st.download_button(
                                label="📥 Download Personas JSON",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"personas_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                            st.success(f"✅ Exported {len(personas)} personas!")
                        else:
                            st.warning("ℹ️ No personas to export")
                except Exception as e:
                    st.error(f"❌ Error exporting personas: {e}")
        
        with col2:
            if st.button("🗑️ Delete All Personas", type="secondary", help="⚠️ DESTROYS ALL PERSONA DATA"):
                st.warning("⚠️ This will DELETE ALL persona data!")
                if st.button("🔥 CONFIRM PERSONA DESTRUCTION", type="primary"):
                    try:
                        with st.spinner("Deleting all personas..."):
                            from app.database import delete_all_personas
                            result = delete_all_personas()
                            if result:
                                st.success("✅ All personas deleted successfully!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete personas")
                    except Exception as e:
                        st.error(f"❌ Error deleting personas: {e}")
    
    def render_user_management_ui(self):
        """Render the user management UI for admin users."""
        st.markdown("# 👤 User Management")
        st.markdown("---")
        
        st.markdown("""
        ### User Management Overview
        
        This tool allows you to manage user accounts:
        - **View all registered users** and their details
        - **Monitor user activity** and account status
        - **Manage user accounts** (activate/deactivate)
        - **View user data statistics** and storage usage
        - **Export user data** for backup
        """)
        
        # System Overview
        st.markdown("### 📊 System Overview")
        try:
            from app.database import QDRANT_CLIENT
            from app.auth.user_management import UserManager
            
            # Get user manager instance
            user_manager = UserManager(QDRANT_CLIENT)  # type: ignore[arg-type]
            
            # Get all users
            all_users = user_manager.get_all_users()
            
            # Calculate system statistics
            total_users = len(all_users)
            active_users = len([u for u in all_users if u.get('is_active', True)])
            inactive_users = total_users - active_users
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", total_users)
            with col2:
                st.metric("Active Users", active_users)
            with col3:
                st.metric("Inactive Users", inactive_users)
            with col4:
                st.metric("System Health", "🟢 Healthy" if total_users > 0 else "🟡 No Users")
            
        except Exception as e:
            st.error(f"❌ Error loading system overview: {e}")
            return
        
        # User List
        st.markdown("### 👥 User List")
        
        if not all_users:
            st.info("ℹ️ No users found in the system.")
            return
        
        # Create user data for display
        user_data = []
        for user in all_users:
            # Get user's data statistics
            user_id = user.get('user_id', '')
            data_stats = self.get_user_data_statistics(user_id)
            
            user_data.append({
                "User ID": user.get('user_id', 'N/A'),
                "Username": user.get('username', 'N/A'),
                "Display Name": user.get('display_name', 'N/A'),
                "Status": "🟢 Active" if user.get('is_active', True) else "🔴 Inactive",
                "Created": user.get('created_at', 'N/A'),
                "Last Login": user.get('last_login', 'Never'),
                "Value Components": data_stats.get('value_components', 0),
                "Personas": data_stats.get('personas', 0),
                "Analyses": data_stats.get('analyses', 0),
                "Storage (MB)": f"{data_stats.get('storage_mb', 0):.1f}"
            })
        
        # Display user table
        import pandas as pd
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # User Operations
        st.markdown("### 🔧 User Operations")
        
        # User selection
        user_options = [user.get('user_id', '') for user in all_users if user.get('user_id')]
        if user_options:
            selected_user_id = st.selectbox("Select User for Operations", user_options)
            
            if selected_user_id:
                # Get selected user details
                selected_user = next((u for u in all_users if u.get('user_id') == selected_user_id), None)
                
                if selected_user:
                    # User details expander
                    with st.expander(f"👤 User Details: {selected_user.get('display_name', selected_user_id)}", expanded=False):
                        self.show_user_details(selected_user)
                    
                    # User operations
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("👁️ View Details", key="view_details"):
                            st.session_state.show_user_details = selected_user_id
                            st.rerun()
                    
                    with col2:
                        if selected_user.get('is_active', True):
                            if st.button("🔴 Deactivate User", key="deactivate_user"):
                                self.deactivate_user(selected_user_id)
                        else:
                            if st.button("🟢 Activate User", key="activate_user"):
                                self.activate_user(selected_user_id)
                    
                    with col3:
                        if st.button("📥 Export User Data", key="export_user_data"):
                            self.export_user_data(selected_user_id)
                    
                    # Dangerous operations
                    st.markdown("### ⚠️ Dangerous Operations")
                    
                    col4, col5 = st.columns(2)
                    
                    with col4:
                        if st.button("🗑️ Delete User Data", type="secondary", key="delete_user_data"):
                            st.warning("⚠️ This will DELETE ALL data for this user!")
                            if st.button("🔥 CONFIRM DATA DELETION", type="primary", key="confirm_delete_data"):
                                self.delete_user_data(selected_user_id)
                    
                    with col5:
                        if st.button("💀 Delete User Account", type="secondary", key="delete_user_account"):
                            st.warning("⚠️ This will DELETE THE USER ACCOUNT AND ALL DATA!")
                            if st.button("🔥 CONFIRM ACCOUNT DELETION", type="primary", key="confirm_delete_account"):
                                self.delete_user_account(selected_user_id)
        
        # Show detailed user view if requested
        if st.session_state.get("show_user_details", False):
            selected_user = next((u for u in all_users if u.get('user_id') == st.session_state.show_user_details), None)
            if selected_user:
                self.show_detailed_user_view(selected_user)
                if st.button("← Back to User List"):
                    st.session_state.show_user_details = False
                    st.rerun()
    
    def get_user_data_statistics(self, user_id: str) -> dict:
        """Get statistics for a specific user's data."""
        try:
            from app.database import QDRANT_CLIENT
            
            stats = {
                'value_components': 0,
                'personas': 0,
                'analyses': 0,
                'storage_mb': 0.0
            }
            
            # Count value components
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                value_components_filter = Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                )
                value_components_result = QDRANT_CLIENT.scroll(
                    collection_name="value_components",
                    scroll_filter=value_components_filter,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                stats['value_components'] = len(value_components_result[0])
            except Exception:
                pass
            
            # Count personas
            try:
                personas_filter = Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                )
                personas_result = QDRANT_CLIENT.scroll(
                    collection_name="personas",
                    scroll_filter=personas_filter,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                stats['personas'] = len(personas_result[0])
            except Exception:
                pass
            
            # Count analyses
            try:
                analyses_filter = Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                )
                analyses_result = QDRANT_CLIENT.scroll(
                    collection_name="value_waterfall_analyses",
                    scroll_filter=analyses_filter,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                stats['analyses'] = len(analyses_result[0])
            except Exception:
                pass
            
            # Estimate storage (rough calculation)
            total_items = stats['value_components'] + stats['personas'] + stats['analyses']
            stats['storage_mb'] = total_items * 0.1  # Rough estimate: 0.1 MB per item
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {'value_components': 0, 'personas': 0, 'analyses': 0, 'storage_mb': 0.0}
    
    def show_user_details(self, user: dict):
        """Show basic user details in expander."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Profile Information:**")
            st.write(f"**User ID**: {user.get('user_id', 'N/A')}")
            st.write(f"**Username**: {user.get('username', 'N/A')}")
            st.write(f"**Display Name**: {user.get('display_name', 'N/A')}")
            st.write(f"**Status**: {'🟢 Active' if user.get('is_active', True) else '🔴 Inactive'}")
        
        with col2:
            st.markdown("**Account Information:**")
            st.write(f"**Created**: {user.get('created_at', 'N/A')}")
            st.write(f"**Last Login**: {user.get('last_login', 'Never')}")
            st.write(f"**Login Count**: {user.get('login_count', 0)}")
    
    def show_detailed_user_view(self, user: dict):
        """Show detailed user information in full view."""
        st.markdown(f"# 👤 User Details: {user.get('display_name', user.get('user_id', 'Unknown'))}")
        st.markdown("---")
        
        # Profile Information
        st.markdown("### 📋 Profile Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basic Information:**")
            st.write(f"**User ID**: {user.get('user_id', 'N/A')}")
            st.write(f"**Username**: {user.get('username', 'N/A')}")
            st.write(f"**Display Name**: {user.get('display_name', 'N/A')}")
            st.write(f"**Email**: {user.get('email', 'N/A')}")
        
        with col2:
            st.markdown("**Account Status:**")
            st.write(f"**Status**: {'🟢 Active' if user.get('is_active', True) else '🔴 Inactive'}")
            st.write(f"**Created**: {user.get('created_at', 'N/A')}")
            st.write(f"**Last Login**: {user.get('last_login', 'Never')}")
            st.write(f"**Login Count**: {user.get('login_count', 0)}")
        
        # Data Summary
        st.markdown("### 📊 Data Summary")
        user_id = user.get('user_id', '')
        data_stats = self.get_user_data_statistics(user_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Value Components", data_stats['value_components'])
        with col2:
            st.metric("Personas", data_stats['personas'])
        with col3:
            st.metric("Analyses", data_stats['analyses'])
        with col4:
            st.metric("Storage", f"{data_stats['storage_mb']:.1f} MB")
        
        # Account Actions
        st.markdown("### 🔧 Account Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if user.get('is_active', True):
                if st.button("🔴 Deactivate Account", key="deactivate_detailed"):
                    self.deactivate_user(user_id)
            else:
                if st.button("🟢 Activate Account", key="activate_detailed"):
                    self.activate_user(user_id)
        
        with col2:
            if st.button("📥 Export User Data", key="export_detailed"):
                self.export_user_data(user_id)
        
        with col3:
            if st.button("🔄 Reset Password", key="reset_password"):
                self.reset_user_password(user_id)
    
    def deactivate_user(self, user_id: str):
        """Deactivate a user account."""
        try:
            from app.auth.user_management import UserManager
            from app.database import QDRANT_CLIENT
            
            user_manager = UserManager(QDRANT_CLIENT)  # type: ignore[arg-type]
            success = user_manager.update_user_status(user_id, is_active=False)
            
            if success:
                st.success(f"✅ User {user_id} deactivated successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to deactivate user {user_id}")
        except Exception as e:
            st.error(f"❌ Error deactivating user: {e}")
    
    def activate_user(self, user_id: str):
        """Activate a user account."""
        try:
            from app.auth.user_management import UserManager
            from app.database import QDRANT_CLIENT
            
            user_manager = UserManager(QDRANT_CLIENT)  # type: ignore[arg-type]
            success = user_manager.update_user_status(user_id, is_active=True)
            
            if success:
                st.success(f"✅ User {user_id} activated successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to activate user {user_id}")
        except Exception as e:
            st.error(f"❌ Error activating user: {e}")
    
    def export_user_data(self, user_id: str):
        """Export user data as JSON."""
        try:
            with st.spinner("Exporting user data..."):
                from app.database import QDRANT_CLIENT
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                import json
                from datetime import datetime
                
                # Get user profile
                from app.auth.user_management import UserManager
                user_manager = UserManager(QDRANT_CLIENT)  # type: ignore[arg-type]
                user_profile = user_manager.get_user_by_id(user_id)
                
                # Get user's data
                user_filter = Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                )
                
                export_data = {
                    "export_date": datetime.now().isoformat(),
                    "user_profile": user_profile,
                    "value_components": [],
                    "personas": [],
                    "analyses": []
                }
                
                # Export value components
                try:
                    vc_result = QDRANT_CLIENT.scroll(
                        collection_name="value_components",
                        scroll_filter=user_filter,
                        limit=1000,
                        with_payload=True,
                        with_vectors=False
                    )
                    export_data["value_components"] = [point.payload for point in vc_result[0]]
                except Exception:
                    pass
                
                # Export personas
                try:
                    personas_result = QDRANT_CLIENT.scroll(
                        collection_name="personas",
                        scroll_filter=user_filter,
                        limit=1000,
                        with_payload=True,
                        with_vectors=False
                    )
                    export_data["personas"] = [point.payload for point in personas_result[0]]
                except Exception:
                    pass
                
                # Export analyses
                try:
                    analyses_result = QDRANT_CLIENT.scroll(
                        collection_name="value_waterfall_analyses",
                        scroll_filter=user_filter,
                        limit=1000,
                        with_payload=True,
                        with_vectors=False
                    )
                    export_data["analyses"] = [point.payload for point in analyses_result[0]]
                except Exception:
                    pass
                
                # Create download button
                st.download_button(
                    label="📥 Download User Data JSON",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name=f"user_data_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                st.success(f"✅ User data exported successfully!")
                
        except Exception as e:
            st.error(f"❌ Error exporting user data: {e}")
    
    def delete_user_data(self, user_id: str):
        """Delete all data for a specific user."""
        try:
            with st.spinner("Deleting user data..."):
                from app.database import QDRANT_CLIENT
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                
                user_filter = Filter(
                    must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]  # type: ignore[arg-type]
                )
                
                deleted_count = 0
                
                # Delete value components
                try:
                    vc_result = QDRANT_CLIENT.scroll(
                        collection_name="value_components",
                        scroll_filter=user_filter,
                        limit=1000,
                        with_payload=False,
                        with_vectors=False
                    )
                    if vc_result[0]:
                        point_ids = [point.id for point in vc_result[0]]
                        QDRANT_CLIENT.delete(
                            collection_name="value_components",
                            points_selector=point_ids
                        )
                        deleted_count += len(point_ids)
                except Exception:
                    pass
                
                # Delete personas
                try:
                    personas_result = QDRANT_CLIENT.scroll(
                        collection_name="personas",
                        scroll_filter=user_filter,
                        limit=1000,
                        with_payload=False,
                        with_vectors=False
                    )
                    if personas_result[0]:
                        point_ids = [point.id for point in personas_result[0]]
                        QDRANT_CLIENT.delete(
                            collection_name="personas",
                            points_selector=point_ids
                        )
                        deleted_count += len(point_ids)
                except Exception:
                    pass
                
                # Delete analyses
                try:
                    analyses_result = QDRANT_CLIENT.scroll(
                        collection_name="value_waterfall_analyses",
                        scroll_filter=user_filter,
                        limit=1000,
                        with_payload=False,
                        with_vectors=False
                    )
                    if analyses_result[0]:
                        point_ids = [point.id for point in analyses_result[0]]
                        QDRANT_CLIENT.delete(
                            collection_name="value_waterfall_analyses",
                            points_selector=point_ids
                        )
                        deleted_count += len(point_ids)
                except Exception:
                    pass
                
                st.success(f"✅ Deleted {deleted_count} data points for user {user_id}!")
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error deleting user data: {e}")
    
    def delete_user_account(self, user_id: str):
        """Delete user account and all data."""
        try:
            # First delete all user data
            self.delete_user_data(user_id)
            
            # Then delete the user account
            with st.spinner("Deleting user account..."):
                from app.auth.user_management import UserManager
                from app.database import QDRANT_CLIENT
                
                user_manager = UserManager(QDRANT_CLIENT)  # type: ignore[arg-type]
                success = user_manager.delete_user(user_id)
                
                if success:
                    st.success(f"✅ User account {user_id} deleted successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ Failed to delete user account {user_id}")
                    
        except Exception as e:
            st.error(f"❌ Error deleting user account: {e}")
    
    def reset_user_password(self, user_id: str):
        """Reset user password using the new password management system."""
        try:
            from app.auth.user_management import UserManager
            from app.database import QDRANT_CLIENT
            
            user_manager = UserManager(QDRANT_CLIENT)  # type: ignore[arg-type]
            result = user_manager.reset_user_password(user_id)
            
            if result.get("success"):
                st.success("✅ Password reset successfully!")
                st.info(f"**Temporary Password**: `{result['temporary_password']}`")
                st.warning("⚠️ User will be required to change password on next login.")
                return result
            else:
                st.error(f"❌ Password reset failed: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            st.error(f"❌ Error resetting password: {e}")
            return None
    

    
    # ============================================================================
    # PASSWORD MANAGEMENT UI
    # ============================================================================
    
    def render_password_management_ui(self):
        """Render the password management UI."""
        st.markdown("# 🔐 Password Management")
        st.markdown("---")
        
        st.markdown("""
        ### Admin Password Reset
        
        This tool allows administrators to reset user passwords:
        - **Reset any user's password** with a secure temporary password
        - **Force password change** on next login for security
        - **Track password resets** for audit purposes
        """)
        
        try:
            from app.auth.user_management import UserManager
            from app.database import QDRANT_CLIENT
            
            user_manager = UserManager(QDRANT_CLIENT)  # type: ignore[arg-type]
            all_users = user_manager.get_all_users()
            
            if not all_users:
                st.info("ℹ️ No users found in the system.")
                return
            
            # User selection
            st.markdown("### 👤 Select User for Password Reset")
            
            user_options = [user.get('user_id', '') for user in all_users if user.get('user_id')]
            selected_user_id = st.selectbox("Choose User", user_options)
            
            if selected_user_id:
                selected_user = next((u for u in all_users if u.get('user_id') == selected_user_id), None)
                
                if selected_user:
                    # Display user info
                    st.markdown("#### 📋 User Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User ID**: {selected_user.get('user_id', 'N/A')}")
                        st.write(f"**Username**: {selected_user.get('username', 'N/A')}")
                        st.write(f"**Display Name**: {selected_user.get('display_name', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Status**: {'🟢 Active' if selected_user.get('is_active', True) else '🔴 Inactive'}")
                        st.write(f"**Created**: {selected_user.get('created_at', 'N/A')}")
                        st.write(f"**Last Login**: {selected_user.get('last_login', 'Never')}")
                    
                    # Password reset section
                    st.markdown("### 🔄 Password Reset")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🔐 Reset Password", type="primary"):
                            result = user_manager.reset_user_password(selected_user_id)
                            
                            if result.get("success"):
                                st.success("✅ Password reset successfully!")
                                st.info(f"**Temporary Password**: `{result['temporary_password']}`")
                                st.warning("⚠️ User will be required to change password on next login.")
                                
                                # Store result in session state for display
                                st.session_state.password_reset_result = result
                            else:
                                st.error(f"❌ Password reset failed: {result.get('error', 'Unknown error')}")
                    
                    with col2:
                        if st.button("📋 Copy Password", disabled=not st.session_state.get("password_reset_result")):
                            result = st.session_state.get("password_reset_result")
                            if result:
                                st.code(result.get("temporary_password", ""))
                    
                    # Show recent password reset result
                    if st.session_state.get("password_reset_result"):
                        result = st.session_state.password_reset_result
                        st.markdown("#### 📋 Last Password Reset")
                        
                        with st.expander("Reset Details", expanded=False):
                            st.write(f"**User**: {result.get('username', 'N/A')}")
                            st.write(f"**Temporary Password**: `{result.get('temporary_password', 'N/A')}`")
                            st.write(f"**Reset Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            if st.button("🗑️ Clear Reset History"):
                                st.session_state.password_reset_result = None
                                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error in password management: {e}")
    
    # ============================================================================
    # DATA OPERATIONS UI
    # ============================================================================
    
    def run(self):
        """Run the main application."""
        # Set page config
        st.set_page_config(
            page_title="Value Rollercoaster - Authenticated",
            page_icon="🎢",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # --- Initialize all session state keys (like original app) ---
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Value Components"
        if "global_processing" not in st.session_state:
            st.session_state["global_processing"] = False
        if "main_tab_selectbox" not in st.session_state:
            st.session_state["main_tab_selectbox"] = 0
        if "main_tab_radio" not in st.session_state:
            st.session_state["main_tab_radio"] = 0
        if "selected_main_category" not in st.session_state:
            st.session_state["selected_main_category"] = "Summary"
        if "selected_persona_id" not in st.session_state:
            st.session_state["selected_persona_id"] = None
        
        # Initialize auth components early for session restoration
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            self._initialize_auth_components()
        
        # Ensure session_manager is initialized
        if self.session_manager is None:
            return
        
        # Try to restore session on app startup
        if not self.session_manager.is_authenticated():
            self.session_manager.restore_session()
        
        # --- App-wide spinner overlay (like original app) ---
        if st.session_state.get('global_processing', False):
            st.markdown(
                '''
                <div style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;
                            background:rgba(255,255,255,0.7);display:flex;align-items:center;justify-content:center;">
                    <div>
                        <img src="https://i.gifer.com/ZZ5H.gif" width="80"/>
                        <p style="font-size:1.5em;">Processing, please wait...</p>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
        
        # Add custom CSS
        st.markdown("""
        <style>
        /* Double the margin after page titles across the entire app */
        .stMarkdown h1 {
            margin-bottom: 4rem !important;
        }
        
        .main-header {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .user-info {
            background-color: #e8f4fd;
            padding: 0.5rem;
            border-radius: 0.3rem;
            margin: 0.5rem 0;
        }
        
        /* Center authentication forms */
        .auth-form-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 60vh;
        }
        

        </style>
        """, unsafe_allow_html=True)
        
        # Render sidebar
        self.render_sidebar()
        
        # Render main content
        self.render_main_content()
    
    def render_company_profile_ui(self):
        """Render company profile management interface"""
        st.title("🏢 Company Profile Management")
        st.markdown("---")
        
        # Import the company setup wizard
        from app.admin.company_setup_wizard import CompanySetupWizard
        from app.core.company_context_manager import CompanyContextManager
        
        # Check if company profile exists
        company_context = CompanyContextManager()
        
        # Refresh the company context to get the latest profile
        company_context.refresh_profile()
        
        # Show company setup wizard if requested (edit mode)
        if st.session_state.get("show_company_wizard", False):
            wizard = CompanySetupWizard()
            wizard.render_setup_wizard()
            
            if st.button("❌ Cancel", help="Close the setup wizard"):
                st.session_state.show_company_wizard = False
                st.rerun()
        else:
            # Show current profile view (normal mode)
            if company_context.is_setup_complete():
                st.success("✅ Company profile is configured")
                
                # Display comprehensive company information with tabs
                st.markdown("### 📋 Company Profile Overview")
                
                # Get the full profile data
                profile = company_context.company_profile
                
                # Create tabs for better organization
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🏢 Basic Info", 
                    "🎯 Market & Business", 
                    "🛠️ Products & Services", 
                    "🧠 Business Intelligence", 
                    "🎨 Branding"
                ])
                
                with tab1:
                    st.markdown("#### Company Information")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Company Name:** {profile.get('company_name', 'N/A')}")
                        st.markdown(f"**Company Size:** {profile.get('company_size', 'N/A')}")
                        st.markdown(f"**Location:** {profile.get('location', 'N/A')}")
                        st.markdown(f"**Location Type:** {profile.get('location_type', 'N/A')}")
                    
                    with col2:
                        # Convert setup date to human-readable format
                        setup_date = profile.get('setup_date', 'N/A')
                        if setup_date != 'N/A':
                            try:
                                from datetime import datetime
                                # Parse the ISO format date
                                dt = datetime.fromisoformat(setup_date.replace('Z', '+00:00'))
                                # Format as human-readable
                                human_date = dt.strftime("%B %d, %Y at %I:%M %p")
                                st.markdown(f"**Setup Date:** {human_date}")
                            except:
                                st.markdown(f"**Setup Date:** {setup_date}")
                        else:
                            st.markdown(f"**Setup Date:** {setup_date}")
                        st.markdown(f"**Core Business:** {profile.get('core_business', 'N/A')}")
                
                with tab2:
                    st.markdown("#### Target Market")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        target_customers = profile.get('target_customers', [])
                        if target_customers:
                            st.markdown(f"**Target Customers:** {', '.join(target_customers)}")
                        else:
                            st.markdown("**Target Customers:** N/A")
                    
                    with col2:
                        industries = profile.get('industries_served', [])
                        if industries:
                            st.markdown(f"**Industries Served:** {', '.join(industries)}")
                        else:
                            st.markdown("**Industries Served:** N/A")
                
                with tab3:
                    st.markdown("#### Products & Services")
                    
                    products = profile.get('products', 'N/A')
                    if products and products != 'N/A':
                        st.markdown(f"**Products & Services:**")
                        st.info(products)
                    else:
                        st.markdown("**Products & Services:** N/A")
                    
                    value_propositions = profile.get('value_propositions', 'N/A')
                    if value_propositions and value_propositions != 'N/A':
                        st.markdown(f"**Value Propositions:**")
                        st.info(value_propositions)
                    else:
                        st.markdown("**Value Propositions:** N/A")
                
                with tab4:
                    st.markdown("#### Business Intelligence")
                    bi_data = profile.get('business_intelligence', {})
                    
                    if bi_data:
                        # Company Classification
                        with st.expander("🏢 Company Classification", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Company Type:** {bi_data.get('company_type', 'N/A')}")
                                st.markdown(f"**Business Model:** {bi_data.get('business_model', 'N/A')}")
                            with col2:
                                st.markdown(f"**Value Delivery:** {bi_data.get('value_delivery_method', 'N/A')}")
                                st.markdown(f"**Market Position:** {bi_data.get('market_position', 'N/A')}")
                        
                        # Company Characteristics
                        with st.expander("📊 Company Characteristics", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Company Size (BI):** {bi_data.get('company_size', 'N/A')}")
                                st.markdown(f"**Maturity Stage:** {bi_data.get('maturity_stage', 'N/A')}")
                            with col2:
                                st.markdown(f"**Geographic Scope:** {bi_data.get('geographic_scope', 'N/A')}")
                                st.markdown(f"**Industry Focus:** {bi_data.get('industry_focus', 'N/A')}")
                        
                        # Business Operations
                        with st.expander("💼 Business Operations", expanded=False):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**Revenue Model:** {bi_data.get('revenue_model', 'N/A')}")
                                st.markdown(f"**Customer Relations:** {bi_data.get('customer_relationship_type', 'N/A')}")
                            with col2:
                                st.markdown(f"**Innovation Focus:** {bi_data.get('innovation_focus', 'N/A')}")
                                st.markdown(f"**Competitive Advantage:** {bi_data.get('competitive_advantage_type', 'N/A')}")
                    else:
                        st.info("No business intelligence data available.")
                
                with tab5:
                    st.markdown("#### Branding & Visual Identity")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        primary_color = profile.get('primary_color', 'N/A')
                        if primary_color and primary_color != 'N/A':
                            st.markdown(f"**Primary Color:** {primary_color}")
                            # Show color preview
                            st.markdown(f'<div style="width: 100px; height: 30px; background-color: {primary_color}; border: 1px solid #ccc; border-radius: 5px; margin: 10px 0;"></div>', unsafe_allow_html=True)
                        else:
                            st.markdown("**Primary Color:** N/A")
                    
                    with col2:
                        logo_url = profile.get('logo_url', 'N/A')
                        if logo_url and logo_url != 'N/A':
                            st.markdown(f"**Logo URL:** {logo_url}")
                            # Try to display logo if it's a valid URL
                            try:
                                st.image(logo_url, width=100, caption="Company Logo")
                            except:
                                st.markdown("*Logo URL provided but image could not be loaded*")
                        else:
                            st.markdown("**Logo URL:** N/A")
                
                st.markdown("---")
                
                # Update button
                if st.button("🔄 Update Company Profile", type="primary", use_container_width=True):
                    st.session_state.show_company_wizard = True
                    st.rerun()
            else:
                st.warning("⚠️ Company profile is not configured")
                st.markdown("Set up your company profile to customize the application for your business.")
                
                if st.button("🚀 Setup Company Profile", type="primary", use_container_width=True):
                    st.session_state.show_company_wizard = True
                    st.rerun()
    
    def render_ai_framework_ui(self):
        """Render the AI Framework admin view"""
        try:
            from app.admin.ai_framework import render_ai_framework_view
            render_ai_framework_view()
        except Exception as e:
            st.error(f"Error loading AI Framework view: {e}")
            logger.error(f"Error in AI Framework view: {e}", exc_info=True)
    
    def render_company_website_ui(self):
        """Render the company website management UI for admin users."""
        st.markdown("# 🌐 Company Website Management")
        st.markdown("---")
        
        # Import and render the company website manager
        try:
            from app.admin.company_website_manager import render_company_website_admin
            render_company_website_admin()
        except Exception as e:
            st.error(f"Error loading company website manager: {e}")
            logger.error(f"Error loading company website manager: {e}")

def main():
    """Main entry point for the authenticated application."""
    try:
        ui = AuthenticatedUI()
        ui.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main() 