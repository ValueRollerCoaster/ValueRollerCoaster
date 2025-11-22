"""
Robust Save Handler

This module provides robust save operations with timeout, cancellation,
and proper error handling to prevent race conditions and hanging states.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable
import streamlit as st
from .operation_manager import (
    get_operation_manager, 
    managed_operation, 
    create_operation_id,
    is_operation_running,
    cancel_operation_if_running
)

class RobustSaveHandler:
    """Handles save operations with robustness features"""
    
    def __init__(self):
        self.operation_manager = get_operation_manager()
        self.save_timeout = 30.0  # 30 seconds default timeout
        self.max_retries = 2
    
    async def save_with_robustness(
        self,
        operation_type: str,
        save_function: Callable,
        *args,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a save operation with robustness features
        
        Args:
            operation_type: Type of operation (e.g., 'save_components', 'save_persona')
            save_function: The actual save function to execute
            *args: Arguments for the save function
            timeout: Custom timeout (defaults to self.save_timeout)
            **kwargs: Keyword arguments for the save function
            
        Returns:
            Dict with success status and any results/errors
        """
        operation_id = create_operation_id(operation_type, "save")
        
        # Check if operation is already running
        if is_operation_running(operation_id):
            logging.warning(f"Operation {operation_id} already running, cancelling previous")
            cancel_operation_if_running(operation_id)
        
        try:
            async with managed_operation(operation_id, operation_type, timeout or self.save_timeout):
                # Execute the save function with timeout
                result = await asyncio.wait_for(
                    self._execute_save_function(save_function, *args, **kwargs),
                    timeout=timeout or self.save_timeout
                )
                
                return {
                    "success": True,
                    "operation_id": operation_id,
                    "result": result,
                    "timestamp": time.time()
                }
                
        except asyncio.TimeoutError:
            logging.error(f"Save operation {operation_id} timed out after {timeout or self.save_timeout}s")
            return {
                "success": False,
                "error": "Operation timed out",
                "operation_id": operation_id,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logging.error(f"Save operation {operation_id} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation_id": operation_id,
                "timestamp": time.time()
            }
    
    async def _execute_save_function(self, save_function: Callable, *args, **kwargs):
        """Execute the save function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(save_function):
                    return await save_function(*args, **kwargs)
                else:
                    return save_function(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    logging.warning(f"Save attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(1)  # Brief delay before retry
                else:
                    logging.error(f"All save attempts failed: {e}")
                    raise e
        
        if last_exception:
            raise last_exception
        raise RuntimeError("Save function failed with no exception")
    
    def create_save_button_handler(
        self,
        operation_type: str,
        save_function: Callable,
        button_text: str,
        button_key: str,
        timeout: Optional[float] = None,
        **button_kwargs
    ) -> Callable:
        """
        Create a robust save button handler
        
        Args:
            operation_type: Type of operation
            save_function: Function to execute on save
            button_text: Text for the button
            button_key: Unique key for the button
            timeout: Custom timeout
            **button_kwargs: Additional button parameters
            
        Returns:
            Function that can be used as a button handler
        """
        
        async def robust_save_handler(*args, **kwargs):
            """Robust save handler with proper error handling"""
            operation_id = create_operation_id(operation_type, "button_click")
            
            try:
                # Check if already processing
                if st.session_state.get("global_processing", False):
                    st.warning("⚠️ Another operation is in progress. Please wait.")
                    return
                
                # Execute save with robustness
                result = await self.save_with_robustness(
                    operation_type=operation_type,
                    save_function=save_function,
                    timeout=timeout,
                    *args,
                    **kwargs
                )
                
                if result["success"]:
                    st.success("✅ Save completed successfully!")
                    st.toast("✅ Save completed successfully!", icon="✅")
                    st.rerun()
                else:
                    error_msg = result.get("error", "Unknown error")
                    st.error(f"❌ Save failed: {error_msg}")
                    st.toast(f"❌ Save failed: {error_msg}", icon="❌")
                    
            except Exception as e:
                logging.error(f"Save button handler error: {e}")
                st.error(f"❌ Unexpected error: {e}")
                st.toast(f"❌ Unexpected error: {e}", icon="❌")
        
        return robust_save_handler
    
    def create_robust_save_button(
        self,
        operation_type: str,
        save_function: Callable,
        button_text: str,
        button_key: str,
        timeout: Optional[float] = None,
        disabled: bool = False,
        **button_kwargs
    ):
        """
        Create a robust save button with built-in protection
        
        Args:
            operation_type: Type of operation
            save_function: Function to execute on save
            button_text: Text for the button
            button_key: Unique key for the button
            timeout: Custom timeout
            disabled: Whether button should be disabled
            **button_kwargs: Additional button parameters
        """
        
        # Check if any operations are running
        is_processing = st.session_state.get("global_processing", False)
        
        # Create button with proper disabled state
        button_disabled = disabled or is_processing
        
        if button_disabled and is_processing:
            st.info("🔄 Processing in progress... Please wait for the current operation to complete.")
        
        # Create the button
        if st.button(
            button_text,
            key=button_key,
            disabled=button_disabled,
            help="Click to save all changes" if not button_disabled else "Operation in progress",
            type="primary",
            **button_kwargs
        ):
            # Create and execute the robust handler
            handler = self.create_save_button_handler(
                operation_type=operation_type,
                save_function=save_function,
                button_text=button_text,
                button_key=button_key,
                timeout=timeout
            )
            
            # Execute the handler
            asyncio.run(handler())

# Global robust save handler instance
_robust_save_handler = RobustSaveHandler()

def get_robust_save_handler() -> RobustSaveHandler:
    """Get the global robust save handler instance"""
    return _robust_save_handler

def create_robust_save_button(
    operation_type: str,
    save_function: Callable,
    button_text: str,
    button_key: str,
    timeout: Optional[float] = None,
    disabled: bool = False,
    **button_kwargs
):
    """Convenience function to create a robust save button"""
    handler = get_robust_save_handler()
    return handler.create_robust_save_button(
        operation_type=operation_type,
        save_function=save_function,
        button_text=button_text,
        button_key=button_key,
        timeout=timeout,
        disabled=disabled,
        **button_kwargs
    )

def execute_robust_save(
    operation_type: str,
    save_function: Callable,
    timeout: Optional[float] = None,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function to execute a robust save operation"""
    handler = get_robust_save_handler()
    return asyncio.run(handler.save_with_robustness(
        operation_type=operation_type,
        save_function=save_function,
        timeout=timeout,
        *args,
        **kwargs
    ))
