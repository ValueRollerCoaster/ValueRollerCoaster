"""
Authentication UI Components
Provides Streamlit UI components for login, registration, and user management.
"""

import streamlit as st
import logging
from typing import Optional, Callable
from .session_manager import SessionManager

logger = logging.getLogger(__name__)

def render_login_form(session_manager: SessionManager, on_success: Optional[Callable] = None) -> bool:
    """
    Render login form and handle authentication.
    
    Args:
        session_manager: Session manager instance
        on_success: Callback function to call on successful login
        
    Returns:
        True if login successful, False otherwise
    """
    st.markdown("## Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        remember_me = st.checkbox("Remember me", value=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            login_submitted = st.form_submit_button("Login", type="primary")
        
        with col2:
            register_clicked = st.form_submit_button("Register New User")
        
        if login_submitted and username and password:
            if session_manager.login_user(username, password):
                st.success(f"Welcome back, {username}!")
                if on_success:
                    on_success()
                return True
            else:
                st.error("Invalid username or password.")
                return False
        
        if register_clicked:
            st.session_state.show_register = True
            st.rerun()
    
    return False

def render_register_form(session_manager: SessionManager, on_success: Optional[Callable] = None) -> bool:
    """
    Render registration form and handle user creation.
    
    Args:
        session_manager: Session manager instance
        on_success: Callback function to call on successful registration
        
    Returns:
        True if registration successful, False otherwise
    """
    st.markdown("## 📝 Create New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username", key="register_username")
        display_name = st.text_input("Display Name", key="register_display_name")
        password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            register_submitted = st.form_submit_button("Create Account", type="primary")
        
        with col2:
            back_to_login = st.form_submit_button("Back to Login")
        
        if back_to_login:
            st.session_state.show_register = False
            st.rerun()
        
        if register_submitted:
            if not username or not password:
                st.error("Username and password are required.")
                return False
            
            if password != confirm_password:
                st.error("Passwords do not match.")
                return False
            
            if len(password) < 3:
                st.error("Password must be at least 3 characters long.")
                return False
            
            try:
                if session_manager.create_user_and_login(username, password, display_name):
                    st.success(f"Account created successfully! Welcome, {username}!")
                    if on_success:
                        on_success()
                    return True
                else:
                    st.error("Failed to create account. Username might already exist.")
                    return False
            except ValueError as e:
                st.error(str(e))
                return False
    
    return False

def render_user_header(session_manager: SessionManager):
    """Render user header with user info and logout button."""
    if not session_manager.is_authenticated():
        return
    
    display_name = session_manager.get_display_name()
    username = session_manager.get_username()
    
    # User info at the top
    st.markdown(f"### 👤 Welcome, {display_name or username}!")
    
    # Buttons below user info
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("⚙️ Settings", key="user_settings", use_container_width=True):
            st.session_state.show_user_settings = True
    
    with col2:
        if st.button("🚪 Logout", key="logout", use_container_width=True):
            session_manager.logout_user()
            st.rerun()
    
    # NEW: DEMO Mode Checkbox (only show if demo mode is enabled)
    from app.config import ENABLE_DEMO_MODE
    if ENABLE_DEMO_MODE:
        st.markdown("---")  # Add separator
        demo_mode = st.checkbox(
            "🎭 DEMO Mode", 
            value=st.session_state.get("user_demo_mode", False),
            help="Enable demo mode to bypass value component requirements and use demo data",
            key="demo_mode_checkbox"
        )
    else:
        # Demo mode is disabled, so set user_demo_mode to False
        demo_mode = False
        if st.session_state.get("user_demo_mode", False):
            st.session_state.user_demo_mode = False
    
    # Update session state when checkbox changes
    if demo_mode != st.session_state.get("user_demo_mode", False):
        st.session_state.user_demo_mode = demo_mode
        
        # Handle demo mode switching
        if demo_mode:
            # Switching TO demo mode - check if demo data already exists
            from app.components.demo_companies.demo_profile_manager import demo_profile_manager
            
            # Check if there's already demo data for any company
            demo_company_id = demo_profile_manager.get_current_demo_company_id()
            if demo_company_id:
                # Demo data already exists, just switch to demo mode
                demo_profile_manager.switch_to_demo_mode(demo_company_id)
                
                # Restore demo customers from database if they exist
                from app.components.demo_companies.demo_populator import DemoPopulator
                populator = DemoPopulator()
                
                # Get demo company profile to restore customers
                demo_company = demo_profile_manager.get_demo_company_profile(demo_company_id)
                if demo_company and 'demo_customers' in demo_company:
                    st.session_state.demo_customers = demo_company['demo_customers']
                    st.session_state.selected_demo_company = demo_company
                    st.session_state.demo_data_populated = True
                    st.success(f"🎭 Demo mode activated with existing data! {len(demo_company['demo_customers'])} demo customers available.")
                else:
                    st.success(f"🎭 Demo mode activated with existing data!")
            else:
                # No demo data exists yet
                st.info("🎭 Demo mode activated. Please select a demo company to load data.")
            
            st.session_state.demo_mode_toast_shown = False
            st.session_state.user_demo_toast_shown = False
        else:
            # Switching FROM demo mode - clear demo data and reload real data
            from app.components.demo_companies.demo_profile_manager import demo_profile_manager
            demo_profile_manager.switch_to_real_mode()
            
            # Clear demo-related session state
            if "selected_demo_company_id" in st.session_state:
                del st.session_state.selected_demo_company_id
            if "demo_customers" in st.session_state:
                del st.session_state.demo_customers
            if "selected_demo_company" in st.session_state:
                del st.session_state.selected_demo_company
            if "demo_data_populated" in st.session_state:
                del st.session_state.demo_data_populated
            
            # Clear value components and AI processed values to force reload from real data
            if "value_components" in st.session_state:
                del st.session_state.value_components
            if "ai_processed_values" in st.session_state:
                del st.session_state.ai_processed_values
            
            # Clear any demo personas
            if "persona" in st.session_state:
                del st.session_state.persona
            if "selected_persona_id" in st.session_state:
                del st.session_state.selected_persona_id
            
            # Clear cache to ensure fresh data is loaded
            st.cache_data.clear()
            
            st.info("🔄 Switched to real company mode - reloading your data...")
        
        st.rerun()

def render_user_settings(session_manager: SessionManager):
    """Render user settings panel."""
    if not session_manager.is_authenticated():
        return
    
    st.markdown("## ⚙️ User Settings")
    
    current_user = session_manager.get_current_user()
    if not current_user:
        st.error("Unable to load user information.")
        return
    
    with st.form("user_settings_form"):
        st.text_input("Username", value=current_user.get("username", ""), disabled=True)
        
        new_display_name = st.text_input(
            "Display Name", 
            value=current_user.get("display_name", ""),
            key="settings_display_name"
        )
        
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            save_settings = st.form_submit_button("Save Changes", type="primary")
        
        with col2:
            cancel_settings = st.form_submit_button("Cancel")
        
        if cancel_settings:
            st.session_state.show_user_settings = False
            st.rerun()
        
        if save_settings:
            updates = {}
            
            if new_display_name != current_user.get("display_name"):
                updates["display_name"] = new_display_name
            
            if new_password and new_password == confirm_new_password:
                updates["password_hash"] = session_manager.user_manager._hash_password(new_password)
            elif new_password and new_password != confirm_new_password:
                st.error("New passwords do not match.")
                return
            
            if updates:
                if session_manager.user_manager.update_user(current_user["user_id"], updates):
                    st.success("Settings updated successfully!")
                    # Update session
                    session_manager.update_session_user(updates)
                    st.session_state.show_user_settings = False
                    st.rerun()
                else:
                    st.error("Failed to update settings.")

def render_auth_page(session_manager: SessionManager, on_success: Optional[Callable] = None):
    """
    Render the main authentication page (login or register).
    
    Args:
        session_manager: Session manager instance
        on_success: Callback function to call on successful authentication
    """
    st.markdown("# 🎢 Value Rollercoaster")
    
    # Check if user wants to register
    show_register = st.session_state.get("show_register", False)
    
    if show_register:
        success = render_register_form(session_manager, on_success)
        if success:
            st.session_state.show_register = False
    else:
        success = render_login_form(session_manager, on_success)
    
    # Add some helpful information
    st.markdown("---")
    st.markdown("### 💡 Tips:")
    st.markdown("- Use the default account: `default_user` / `default`")
    st.markdown("- Create your own account to keep your data separate")
    st.markdown("- Your data is private and isolated from other users")

def require_auth_page(session_manager: SessionManager, on_success: Optional[Callable] = None):
    """
    Require authentication and show login page if not authenticated.
    
    Args:
        session_manager: Session manager instance
        on_success: Callback function to call on successful authentication
    """
    if not session_manager.is_authenticated():
        render_auth_page(session_manager, on_success)
        st.stop() 