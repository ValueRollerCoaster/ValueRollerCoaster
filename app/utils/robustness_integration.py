"""
Robustness Integration Module

This module provides a comprehensive integration of all robustness features
to prevent race conditions, handle timeouts, and ensure proper state management.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable
import streamlit as st
from datetime import datetime, timedelta

# Import all robustness modules
from .operation_manager import get_operation_manager, force_reset_all_operations
from .robust_save_handler import get_robust_save_handler
from .atomic_state_manager import get_atomic_state_manager
from .operation_tracker import get_operation_tracker, get_operation_stats
from .operation_tracker import cleanup_old_operations as tracker_cleanup_old_operations

class RobustnessManager:
    """Central manager for all robustness features"""
    
    def __init__(self):
        self.operation_manager = get_operation_manager()
        self.save_handler = get_robust_save_handler()
        self.state_manager = get_atomic_state_manager()
        self.tracker = get_operation_tracker()
        self.initialized = False
    
    def initialize(self):
        """Initialize the robustness system"""
        if self.initialized:
            return
        
        try:
            # Initialize session state for robustness
            if "robustness_initialized" not in st.session_state:
                st.session_state["robustness_initialized"] = True
                st.session_state["global_processing"] = False
                st.session_state["operation_count"] = 0
                st.session_state["last_cleanup"] = time.time()
            
            # Clean up old operations
            self.cleanup_old_operations()
            
            # Check for stuck operations
            self.check_and_reset_stuck_operations()
            
            self.initialized = True
            logging.info("Robustness system initialized")
            
        except Exception as e:
            logging.error(f"Failed to initialize robustness system: {e}")
            raise
    
    def cleanup_old_operations(self, max_age_seconds: float = 3600):
        """Clean up old operations"""
        try:
            # Clean up operation tracker
            cleaned_count = tracker_cleanup_old_operations(max_age_seconds)
            
            # Clean up operation manager
            timed_out = self.operation_manager.check_timeouts()
            
            if cleaned_count > 0 or timed_out:
                logging.info(f"Cleaned up {cleaned_count} old operations, {len(timed_out)} timed out")
            
            # Update last cleanup time
            st.session_state["last_cleanup"] = time.time()
            
        except Exception as e:
            logging.error(f"Error cleaning up old operations: {e}")
    
    def check_and_reset_stuck_operations(self):
        """Check for and reset stuck operations"""
        try:
            # Get long-running operations
            long_running = self.tracker.get_long_running_operations(threshold_seconds=120)
            
            if long_running:
                logging.warning(f"Found {len(long_running)} stuck operations, resetting")
                
                for op in long_running:
                    # Cancel the operation
                    self.operation_manager.cancel_operation(op.operation_id)
                    
                    # Update tracker
                    from .operation_tracker import OperationStatus
                    self.tracker.update_operation_status(
                        op.operation_id, 
                        OperationStatus.TIMEOUT, 
                        "Operation was stuck and reset"
                    )
                
                # Force reset all operations if too many are stuck
                if len(long_running) > 3:
                    logging.warning("Too many stuck operations, forcing full reset")
                    force_reset_all_operations()
                    
                    # Show user notification
                    st.warning("⚠️ System detected stuck operations and reset them. Please try again.")
            
        except Exception as e:
            logging.error(f"Error checking stuck operations: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Get operation statistics
            op_stats = self.tracker.get_operation_stats()
            
            # Get active operations
            active_ops = self.tracker.get_active_operations()
            
            # Get operation manager status
            manager_ops = self.operation_manager.get_all_operations()
            
            # Check for timeouts
            timed_out = self.operation_manager.check_timeouts()
            
            return {
                "initialized": self.initialized,
                "active_operations": len(active_ops),
                "operation_manager_ops": len(manager_ops),
                "timed_out_operations": len(timed_out),
                "operation_stats": op_stats,
                "global_processing": st.session_state.get("global_processing", False),
                "last_cleanup": st.session_state.get("last_cleanup", 0),
                "system_health": self._assess_system_health()
            }
            
        except Exception as e:
            logging.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    def _assess_system_health(self) -> str:
        """Assess overall system health"""
        try:
            # Check for too many active operations
            active_count = len(self.tracker.get_active_operations())
            if active_count > 10:
                return "unhealthy"
            
            # Check for long-running operations
            long_running = self.tracker.get_long_running_operations(threshold_seconds=60)
            if len(long_running) > 3:
                return "degraded"
            
            # Check for stuck global processing
            if st.session_state.get("global_processing", False):
                # Check if it's been stuck for too long
                if "global_processing_start" not in st.session_state:
                    st.session_state["global_processing_start"] = time.time()
                elif time.time() - st.session_state["global_processing_start"] > 300:  # 5 minutes
                    return "stuck"
            
            return "healthy"
            
        except Exception as e:
            logging.error(f"Error assessing system health: {e}")
            return "unknown"
    
    def force_system_reset(self):
        """Force reset the entire system (emergency function)"""
        try:
            logging.warning("Force resetting entire robustness system")
            
            # Reset all operations
            force_reset_all_operations()
            
            # Reset state manager
            self.state_manager.safe_state_reset([
                "global_processing",
                "operation_count",
                "global_processing_start"
            ])
            
            # Clear all operation tracking
            self.tracker.operations.clear()
            
            # Reset session state
            st.session_state["global_processing"] = False
            st.session_state["operation_count"] = 0
            
            logging.warning("System reset completed")
            
        except Exception as e:
            logging.error(f"Error in force system reset: {e}")
            raise
    
    def create_robust_save_button(
        self,
        operation_type: str,
        save_function: Callable,
        button_text: str,
        button_key: str,
        timeout: Optional[float] = None,
        **button_kwargs
    ):
        """Create a robust save button with all protections"""
        return self.save_handler.create_robust_save_button(
            operation_type=operation_type,
            save_function=save_function,
            button_text=button_text,
            button_key=button_key,
            timeout=timeout,
            **button_kwargs
        )
    
    async def execute_robust_save(
        self,
        operation_type: str,
        save_function: Callable,
        timeout: Optional[float] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a robust save operation"""
        return await self.save_handler.save_with_robustness(
            operation_type=operation_type,
            save_function=save_function,
            timeout=timeout,
            *args,
            **kwargs
        )

# Global robustness manager instance
_robustness_manager = RobustnessManager()

def get_robustness_manager() -> RobustnessManager:
    """Get the global robustness manager instance"""
    return _robustness_manager

def initialize_robustness_system():
    """Initialize the robustness system (call this at app startup)"""
    manager = get_robustness_manager()
    manager.initialize()

def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status"""
    manager = get_robustness_manager()
    return manager.get_system_status()

def force_system_reset():
    """Force reset the entire system (emergency function)"""
    manager = get_robustness_manager()
    manager.force_system_reset()

def create_robust_save_button(
    operation_type: str,
    save_function: Callable,
    button_text: str,
    button_key: str,
    timeout: Optional[float] = None,
    **button_kwargs
):
    """Create a robust save button with all protections"""
    manager = get_robustness_manager()
    return manager.create_robust_save_button(
        operation_type=operation_type,
        save_function=save_function,
        button_text=button_text,
        button_key=button_key,
        timeout=timeout,
        **button_kwargs
    )

async def execute_robust_save(
    operation_type: str,
    save_function: Callable,
    timeout: Optional[float] = None,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Execute a robust save operation"""
    manager = get_robustness_manager()
    return await manager.execute_robust_save(
        operation_type=operation_type,
        save_function=save_function,
        timeout=timeout,
        *args,
        **kwargs
    )

def cleanup_old_operations(max_age_seconds: float = 3600):
    """Clean up old operations"""
    manager = get_robustness_manager()
    manager.cleanup_old_operations(max_age_seconds)

def check_and_reset_stuck_operations():
    """Check for and reset stuck operations"""
    manager = get_robustness_manager()
    manager.check_and_reset_stuck_operations()

# Convenience functions for common operations
async def robust_save_components(
    operation_type: str,
    save_function: Callable,
    timeout: Optional[float] = None,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for robust save operations"""
    return await execute_robust_save(
        operation_type=operation_type,
        save_function=save_function,
        timeout=timeout,
        *args,
        **kwargs
    )

async def robust_save_persona(
    operation_type: str,
    save_function: Callable,
    timeout: Optional[float] = None,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for robust persona save operations"""
    return await execute_robust_save(
        operation_type=operation_type,
        save_function=save_function,
        timeout=timeout,
        *args,
        **kwargs
    )
