"""
Pre-configured Spinner Contexts

This module provides pre-configured context managers for common operations,
making it easy to use spinners with minimal configuration.
"""

from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import streamlit as st
from .spinner_manager import get_spinner_manager
from .spinner_types import SpinnerConfig, SpinnerType, SpinnerPresets

# Get the global spinner manager
_spinner_manager = get_spinner_manager()

@contextmanager
def save_spinner(count: int = 0, custom_message: Optional[str] = None):
    """
    Context manager for save operations.
    
    Args:
        count: Number of items being saved
        custom_message: Custom message to display
    """
    config = SpinnerPresets.save_components(count)
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def delete_spinner(item_type: str = "item", custom_message: Optional[str] = None):
    """
    Context manager for delete operations.
    
    Args:
        item_type: Type of item being deleted
        custom_message: Custom message to display
    """
    config = SpinnerPresets.delete_operation(item_type)
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def ai_processing_spinner(operation: str, count: int = 0, custom_message: Optional[str] = None):
    """
    Context manager for AI processing operations.
    
    Args:
        operation: Description of the AI operation
        count: Number of items being processed
        custom_message: Custom message to display
    """
    config = SpinnerPresets.ai_processing(operation, count)
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def database_spinner(operation: str, count: int = 0, custom_message: Optional[str] = None):
    """
    Context manager for database operations.
    
    Args:
        operation: Description of the database operation
        count: Number of items being processed
        custom_message: Custom message to display
    """
    config = SpinnerPresets.database_operation(operation, count)
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def ui_refresh_spinner(custom_message: Optional[str] = None):
    """
    Context manager for UI refresh operations.
    
    Args:
        custom_message: Custom message to display
    """
    config = SpinnerPresets.ui_refresh()
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def analysis_spinner(operation: str, custom_message: Optional[str] = None):
    """
    Context manager for analysis operations.
    
    Args:
        operation: Description of the analysis operation
        custom_message: Custom message to display
    """
    config = SpinnerPresets.analysis(operation)
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def search_spinner(query_type: str = "data", custom_message: Optional[str] = None):
    """
    Context manager for search operations.
    
    Args:
        query_type: Type of data being searched
        custom_message: Custom message to display
    """
    config = SpinnerPresets.search(query_type)
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def generate_spinner(item_type: str, custom_message: Optional[str] = None):
    """
    Context manager for generation operations.
    
    Args:
        item_type: Type of item being generated
        custom_message: Custom message to display
    """
    config = SpinnerPresets.generate(item_type)
    if custom_message:
        config.message = custom_message
    
    with _spinner_manager.spinner(config):
        yield

@contextmanager
def dialog_spinner(title: str, message: Optional[str] = None, icon: str = "🔄"):
    """
    Context manager for dialog-based spinner operations with backdrop blur.
    
    Args:
        title: Dialog title
        message: Spinner message (optional, defaults to title)
        icon: Spinner icon
    """
    if message is None:
        message = title
    
    try:
        # Create a full-screen overlay with blur effect
        overlay_html = f"""
        <div style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(5px);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        ">
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                text-align: center;
                max-width: 400px;
            ">
                <div style="font-size: 2rem; margin-bottom: 1rem;">{icon}</div>
                <h3 style="margin-bottom: 1rem; color: #333;">{title}</h3>
                <p style="color: #666; margin-bottom: 1rem;">{message}</p>
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #3498db;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto;
                "></div>
            </div>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """
        
        # Show the overlay
        overlay_placeholder = st.empty()
        overlay_placeholder.markdown(overlay_html, unsafe_allow_html=True)
        
        yield
        
        # Hide the overlay
        overlay_placeholder.empty()
        
    except Exception as e:
        st.error(f"Operation failed: {str(e)}")
        raise

@contextmanager
def multi_step_save_spinner(steps: List[Dict[str, Any]]):
    """
    Context manager for multi-step save operations (like value components).
    
    Args:
        steps: List of step configurations with keys:
               - name: Step name
               - count: Number of items (optional)
               - message: Custom message (optional)
    """
    # For now, just use a simple save spinner
    # This can be enhanced later with proper multi-step support
    total_operations = sum(step.get("count", 0) for step in steps)
    
    with save_spinner(total_operations, "Saving value components..."):
        yield

@contextmanager
def custom_spinner(
    message: str,
    icon: str = "🔄",
    spinner_type: SpinnerType = SpinnerType.PROCESS,
    show_toast: bool = False,
    success_message: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Context manager for custom spinner operations.
    
    Args:
        message: Spinner message
        icon: Spinner icon
        spinner_type: Type of spinner operation
        show_toast: Whether to show toast notifications
        success_message: Custom success message
        error_message: Custom error message
    """
    config = SpinnerConfig(
        type=spinner_type,
        message=message,
        icon=icon,
        show_toast_on_complete=show_toast,
        toast_success_message=success_message,
        toast_error_message=error_message
    )
    
    with _spinner_manager.spinner(config):
        yield

# Convenience functions for common operations
def save_components(count: int = 0):
    """Quick function to save components with spinner."""
    return save_spinner(count)

def delete_item(item_type: str = "item"):
    """Quick function to delete items with spinner."""
    return delete_spinner(item_type)

def process_with_ai(operation: str, count: int = 0):
    """Quick function for AI processing with spinner."""
    return ai_processing_spinner(operation, count)

def refresh_ui():
    """Quick function to refresh UI with spinner."""
    return ui_refresh_spinner()

def analyze_data(operation: str):
    """Quick function for analysis with spinner."""
    return analysis_spinner(operation)

def search_data(query_type: str = "data"):
    """Quick function for search with spinner."""
    return search_spinner(query_type)

def generate_item(item_type: str):
    """Quick function for generation with spinner."""
    return generate_spinner(item_type) 