"""
Operation Manager - Robustness System

This module provides comprehensive operation management to prevent race conditions,
handle timeouts, and ensure proper state management during save operations.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from contextlib import asynccontextmanager
import streamlit as st
from datetime import datetime, timedelta

class OperationManager:
    """Manages operations with timeout, cancellation, and state tracking"""
    
    def __init__(self):
        self.active_operations: Dict[str, Dict[str, Any]] = {}
        self.operation_timeouts: Dict[str, float] = {}
        self.default_timeout = 30.0  # 30 seconds default timeout
    
    def start_operation(self, operation_id: str, operation_type: str, timeout: Optional[float] = None) -> bool:
        """Start tracking an operation"""
        try:
            if operation_id in self.active_operations:
                logging.warning(f"Operation {operation_id} already active, cancelling previous")
                self.cancel_operation(operation_id)
            
            self.active_operations[operation_id] = {
                "type": operation_type,
                "start_time": time.time(),
                "status": "running",
                "timeout": timeout or self.default_timeout
            }
            
            # Set timeout
            self.operation_timeouts[operation_id] = time.time() + (timeout or self.default_timeout)
            
            # Set global processing flag
            st.session_state["global_processing"] = True
            st.session_state[f"operation_{operation_id}"] = True
            
            logging.info(f"Started operation {operation_id} of type {operation_type}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start operation {operation_id}: {e}")
            return False
    
    def complete_operation(self, operation_id: str, success: bool = True) -> bool:
        """Mark an operation as completed"""
        try:
            if operation_id not in self.active_operations:
                logging.warning(f"Operation {operation_id} not found in active operations")
                return False
            
            self.active_operations[operation_id]["status"] = "completed" if success else "failed"
            self.active_operations[operation_id]["end_time"] = time.time()
            
            # Clean up
            del self.active_operations[operation_id]
            if operation_id in self.operation_timeouts:
                del self.operation_timeouts[operation_id]
            
            # Reset session state
            st.session_state[f"operation_{operation_id}"] = False
            
            # Check if any operations are still running
            if not self.active_operations:
                st.session_state["global_processing"] = False
            
            logging.info(f"Completed operation {operation_id} with success={success}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to complete operation {operation_id}: {e}")
            return False
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation"""
        try:
            if operation_id not in self.active_operations:
                return False
            
            # Cancel any associated tasks
            self._cancel_associated_tasks(operation_id)
            
            # Mark as cancelled
            self.active_operations[operation_id]["status"] = "cancelled"
            self.active_operations[operation_id]["end_time"] = time.time()
            
            # Clean up
            del self.active_operations[operation_id]
            if operation_id in self.operation_timeouts:
                del self.operation_timeouts[operation_id]
            
            # Reset session state
            st.session_state[f"operation_{operation_id}"] = False
            
            # Check if any operations are still running
            if not self.active_operations:
                st.session_state["global_processing"] = False
            
            logging.info(f"Cancelled operation {operation_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to cancel operation {operation_id}: {e}")
            return False
    
    def _cancel_associated_tasks(self, operation_id: str):
        """Cancel tasks associated with an operation"""
        try:
            # Cancel AI regeneration tasks
            if "ai_regen_tasks" in st.session_state:
                for task_key, task in st.session_state["ai_regen_tasks"].items():
                    if not task.done() and operation_id in task_key:
                        task.cancel()
                        logging.info(f"Cancelled AI task {task_key}")
            
            # Cancel background tasks
            if "background_tasks" in st.session_state:
                for task_id, task_info in st.session_state["background_tasks"].items():
                    if task_info.get("operation_id") == operation_id:
                        if "task" in task_info and not task_info["task"].done():
                            task_info["task"].cancel()
                            logging.info(f"Cancelled background task {task_id}")
            
        except Exception as e:
            logging.error(f"Error cancelling associated tasks for {operation_id}: {e}")
    
    def check_timeouts(self) -> List[str]:
        """Check for timed out operations and cancel them"""
        timed_out = []
        current_time = time.time()
        
        for operation_id, timeout_time in list(self.operation_timeouts.items()):
            if current_time > timeout_time:
                logging.warning(f"Operation {operation_id} timed out")
                self.cancel_operation(operation_id)
                timed_out.append(operation_id)
        
        return timed_out
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an operation"""
        return self.active_operations.get(operation_id)
    
    def get_all_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active operations"""
        return self.active_operations.copy()
    
    def force_reset_all(self):
        """Force reset all operations (emergency reset)"""
        try:
            # Cancel all operations
            for operation_id in list(self.active_operations.keys()):
                self.cancel_operation(operation_id)
            
            # Reset all processing flags
            st.session_state["global_processing"] = False
            
            # Clear AI processing flags
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and (key.startswith("ai_processing_") or key.startswith("operation_")):
                    st.session_state[key] = False
            
            # Cancel all AI regeneration tasks
            if "ai_regen_tasks" in st.session_state:
                for task_key, task in st.session_state["ai_regen_tasks"].items():
                    if not task.done():
                        task.cancel()
                st.session_state["ai_regen_tasks"] = {}
            
            logging.warning("Force reset all operations completed")
            
        except Exception as e:
            logging.error(f"Error in force reset: {e}")

# Global operation manager instance
_operation_manager = OperationManager()

def get_operation_manager() -> OperationManager:
    """Get the global operation manager instance"""
    return _operation_manager

@asynccontextmanager
async def managed_operation(operation_id: str, operation_type: str, timeout: Optional[float] = None):
    """Context manager for operations with automatic cleanup"""
    manager = get_operation_manager()
    
    try:
        # Start operation
        if not manager.start_operation(operation_id, operation_type, timeout):
            raise RuntimeError(f"Failed to start operation {operation_id}")
        
        yield manager
        
    except Exception as e:
        # Mark operation as failed
        manager.complete_operation(operation_id, success=False)
        logging.error(f"Operation {operation_id} failed: {e}")
        raise
        
    finally:
        # Ensure operation is completed
        manager.complete_operation(operation_id, success=True)

def create_operation_id(operation_type: str, context: str = "") -> str:
    """Create a unique operation ID"""
    timestamp = int(time.time() * 1000)
    return f"{operation_type}_{context}_{timestamp}"

def is_operation_running(operation_id: str) -> bool:
    """Check if an operation is currently running"""
    manager = get_operation_manager()
    return operation_id in manager.active_operations

def cancel_operation_if_running(operation_id: str) -> bool:
    """Cancel an operation if it's running"""
    manager = get_operation_manager()
    if operation_id in manager.active_operations:
        return manager.cancel_operation(operation_id)
    return False

def force_reset_all_operations():
    """Emergency reset for all operations"""
    manager = get_operation_manager()
    manager.force_reset_all()

def check_and_handle_timeouts():
    """Check for timeouts and handle them (call this periodically)"""
    manager = get_operation_manager()
    timed_out = manager.check_timeouts()
    
    if timed_out:
        logging.warning(f"Timed out operations: {timed_out}")
        # Show user notification
        for operation_id in timed_out:
            st.warning(f"⏰ Operation timed out: {operation_id}")
    
    return timed_out
