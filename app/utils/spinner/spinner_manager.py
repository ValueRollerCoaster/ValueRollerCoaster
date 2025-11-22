"""
Spinner Manager

This module provides the main SpinnerManager class that handles all spinner operations,
error handling, and provides a clean interface for managing loading states.
"""

import time
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Callable
import streamlit as st
from .spinner_types import SpinnerConfig, SpinnerContext, SpinnerType
from .progress_tracker import ProgressTracker, MultiStepProgress

class SpinnerManager:
    """Main spinner manager for handling all spinner operations."""
    
    def __init__(self):
        self.active_spinners: Dict[str, SpinnerContext] = {}
        self.progress_trackers: Dict[str, ProgressTracker] = {}
        self.logger = logging.getLogger(__name__)
        self.operation_counter = 0
    
    @contextmanager
    def spinner(self, config: SpinnerConfig, operation_id: Optional[str] = None):
        """
        Context manager for spinner operations with automatic error handling.
        
        Args:
            config: Spinner configuration
            operation_id: Optional unique identifier for the operation
            
        Yields:
            SpinnerContext: Context information for the operation
        """
        if operation_id is None:
            self.operation_counter += 1
            operation_id = f"op_{self.operation_counter}"
        
        context = SpinnerContext(config=config)
        context.start_time = time.time()
        
        # Log operation start
        if config.log_operation:
            # Remove emoji characters for logging to avoid encoding issues
            clean_message = config.message.encode('ascii', 'ignore').decode('ascii')
            self.logger.info(f"[{operation_id}] Starting {config.type.value}: {clean_message}")
        
        try:
            # Show spinner
            with st.spinner(f"{config.icon} {config.message}"):
                # Store context
                self.active_spinners[operation_id] = context
                
                # Yield context for the operation
                yield context
                
                # Mark as successful
                context.success = True
                context.end_time = time.time()
                
                # Show success toast if configured
                if config.show_toast_on_complete and config.toast_success_message:
                    st.toast(config.toast_success_message, icon="✅")
                
                # Log completion
                if config.log_operation:
                    duration = context.end_time - context.start_time
                    self.logger.info(f"[{operation_id}] Completed {config.type.value} in {duration:.2f}s")
                
        except Exception as e:
            # Mark as failed
            context.success = False
            context.error_message = str(e)
            context.end_time = time.time()
            
            # Show error toast if configured
            if config.show_toast_on_complete and config.toast_error_message:
                st.toast(config.toast_error_message, icon="❌")
            else:
                st.toast(f"❌ Operation failed: {str(e)}", icon="❌")
            
            # Log error
            duration = context.end_time - context.start_time
            self.logger.error(f"[{operation_id}] Failed {config.type.value} after {duration:.2f}s: {str(e)}", exc_info=True)
            
            # Re-raise the exception
            raise
        
        finally:
            # Clean up
            if operation_id in self.active_spinners:
                del self.active_spinners[operation_id]
    
    @contextmanager
    def multi_step_spinner(self, steps: List[SpinnerConfig], operation_name: str = "Multi-step Operation"):
        """
        Context manager for multi-step operations with progress tracking.
        
        Args:
            steps: List of spinner configurations for each step
            operation_name: Name of the overall operation
            
        Yields:
            MultiStepProgress: Progress tracker for the operation
        """
        progress = MultiStepProgress(operation_name)
        
        try:
            # Yield progress first so caller can use it
            yield progress
            
            # Execute all steps sequentially
            for i, step_config in enumerate(steps):
                with self.spinner(step_config, f"{operation_name}_step_{i+1}"):
                    # Mark step as completed in progress tracker
                    with progress.step(step_config.message, step_config.message):
                        pass  # The actual work is done by the caller before this point
                        
        except Exception as e:
            self.logger.error(f"[{operation_name}] Multi-step operation failed: {str(e)}", exc_info=True)
            raise
    
    def create_progress_tracker(self, total_steps: int, operation_name: str = "Operation") -> ProgressTracker:
        """Create a progress tracker for an operation."""
        tracker = ProgressTracker(total_steps, operation_name)
        self.progress_trackers[operation_name] = tracker
        return tracker
    
    def get_active_spinners(self) -> Dict[str, SpinnerContext]:
        """Get all currently active spinners."""
        return self.active_spinners.copy()
    
    def get_spinner_context(self, operation_id: str) -> Optional[SpinnerContext]:
        """Get the context for a specific operation."""
        return self.active_spinners.get(operation_id)
    
    def cancel_spinner(self, operation_id: str) -> bool:
        """Cancel a specific spinner operation."""
        if operation_id in self.active_spinners:
            context = self.active_spinners[operation_id]
            context.success = False
            context.error_message = "Operation cancelled"
            context.end_time = time.time()
            
            self.logger.info(f"[{operation_id}] Operation cancelled")
            del self.active_spinners[operation_id]
            return True
        return False
    
    def cancel_all_spinners(self):
        """Cancel all active spinner operations."""
        operation_ids = list(self.active_spinners.keys())
        for operation_id in operation_ids:
            self.cancel_spinner(operation_id)
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get statistics about spinner operations."""
        total_operations = len(self.active_spinners)
        completed_operations = sum(1 for ctx in self.active_spinners.values() if ctx.success)
        failed_operations = total_operations - completed_operations
        
        return {
            "active_operations": total_operations,
            "completed_operations": completed_operations,
            "failed_operations": failed_operations,
            "progress_trackers": len(self.progress_trackers)
        }

class SpinnerDecorator:
    """Decorator for automatically wrapping functions with spinners."""
    
    def __init__(self, spinner_manager: SpinnerManager):
        self.spinner_manager = spinner_manager
    
    def __call__(self, config: SpinnerConfig, operation_id: Optional[str] = None):
        """Decorator that wraps a function with a spinner."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                with self.spinner_manager.spinner(config, operation_id):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

# Global spinner manager instance
_spinner_manager = None

def get_spinner_manager() -> SpinnerManager:
    """Get the global spinner manager instance."""
    global _spinner_manager
    if _spinner_manager is None:
        _spinner_manager = SpinnerManager()
    return _spinner_manager

def with_spinner(config: SpinnerConfig, operation_id: Optional[str] = None):
    """Decorator for wrapping functions with spinners."""
    return SpinnerDecorator(get_spinner_manager())(config, operation_id) 