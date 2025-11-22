"""
Atomic State Manager

This module provides atomic state management to prevent race conditions
and ensure consistent state updates during operations.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager
import streamlit as st
from threading import Lock

class AtomicStateManager:
    """Manages state updates atomically to prevent race conditions"""
    
    def __init__(self):
        self._state_locks: Dict[str, Lock] = {}
        self._operation_locks: Dict[str, Lock] = {}
        self._state_version: Dict[str, int] = {}
    
    def _get_lock(self, key: str, lock_type: str = "state") -> Lock:
        """Get or create a lock for a specific key"""
        lock_key = f"{lock_type}_{key}"
        if lock_key not in self._state_locks:
            self._state_locks[lock_key] = Lock()
        return self._state_locks[lock_key]
    
    def _get_operation_lock(self, operation_id: str) -> Lock:
        """Get or create a lock for a specific operation"""
        if operation_id not in self._operation_locks:
            self._operation_locks[operation_id] = Lock()
        return self._operation_locks[operation_id]
    
    def atomic_state_update(self, key: str, update_function: Callable[[Any], Any], default_value: Any = None):
        """
        Atomically update a state value
        
        Args:
            key: State key to update
            update_function: Function that takes current value and returns new value
            default_value: Default value if key doesn't exist
        """
        lock = self._get_lock(key)
        
        with lock:
            try:
                # Get current value
                current_value = st.session_state.get(key, default_value)
                
                # Apply update function
                new_value = update_function(current_value)
                
                # Update state
                st.session_state[key] = new_value
                
                # Update version for change tracking
                version_key = f"{key}_version"
                self._state_version[version_key] = self._state_version.get(version_key, 0) + 1
                
                logging.debug(f"Atomically updated {key}: {current_value} -> {new_value}")
                
            except Exception as e:
                logging.error(f"Error in atomic state update for {key}: {e}")
                raise
    
    def atomic_batch_update(self, updates: Dict[str, Callable[[Any], Any]], defaults: Optional[Dict[str, Any]] = None):
        """
        Atomically update multiple state values
        
        Args:
            updates: Dict of key -> update_function
            defaults: Dict of key -> default_value
        """
        if not updates:
            return
        
        # Sort keys to prevent deadlocks
        sorted_keys = sorted(updates.keys())
        locks = [self._get_lock(key) for key in sorted_keys]
        
        # Acquire all locks in order
        for lock in locks:
            lock.acquire()
        
        try:
            for key, update_function in updates.items():
                default_value = (defaults or {}).get(key)
                current_value = st.session_state.get(key, default_value)
                new_value = update_function(current_value)
                st.session_state[key] = new_value
                
                # Update version
                version_key = f"{key}_version"
                self._state_version[version_key] = self._state_version.get(version_key, 0) + 1
                
                logging.debug(f"Batch updated {key}: {current_value} -> {new_value}")
                
        except Exception as e:
            logging.error(f"Error in atomic batch update: {e}")
            raise
        finally:
            # Release all locks
            for lock in locks:
                lock.release()
    
    def atomic_operation(self, operation_id: str, operation_function: Callable, *args, **kwargs):
        """
        Execute an operation atomically
        
        Args:
            operation_id: Unique operation identifier
            operation_function: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
        """
        lock = self._get_operation_lock(operation_id)
        
        with lock:
            try:
                logging.debug(f"Starting atomic operation {operation_id}")
                result = operation_function(*args, **kwargs)
                logging.debug(f"Completed atomic operation {operation_id}")
                return result
                
            except Exception as e:
                logging.error(f"Error in atomic operation {operation_id}: {e}")
                raise
    
    def get_state_version(self, key: str) -> int:
        """Get the version number of a state key"""
        version_key = f"{key}_version"
        return self._state_version.get(version_key, 0)
    
    def wait_for_state_change(self, key: str, timeout: float = 5.0) -> bool:
        """
        Wait for a state key to change
        
        Args:
            key: State key to watch
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if state changed, False if timeout
        """
        start_time = time.time()
        initial_version = self.get_state_version(key)
        
        while time.time() - start_time < timeout:
            if self.get_state_version(key) > initial_version:
                return True
            time.sleep(0.1)  # Small delay to prevent busy waiting
        
        return False
    
    def safe_state_reset(self, keys: List[str], reset_values: Optional[Dict[str, Any]] = None):
        """
        Safely reset multiple state keys
        
        Args:
            keys: List of keys to reset
            reset_values: Dict of key -> reset_value (defaults to False)
        """
        if not keys:
            return
        
        # Sort keys to prevent deadlocks
        sorted_keys = sorted(keys)
        locks = [self._get_lock(key) for key in sorted_keys]
        
        # Acquire all locks in order
        for lock in locks:
            lock.acquire()
        
        try:
            for key in keys:
                reset_value = (reset_values or {}).get(key, False)
                st.session_state[key] = reset_value
                
                # Update version
                version_key = f"{key}_version"
                self._state_version[version_key] = self._state_version.get(version_key, 0) + 1
                
                logging.debug(f"Reset {key} to {reset_value}")
                
        except Exception as e:
            logging.error(f"Error in safe state reset: {e}")
            raise
        finally:
            # Release all locks
            for lock in locks:
                lock.release()
    
    def cleanup_operation_locks(self, operation_id: str):
        """Clean up locks for a completed operation"""
        if operation_id in self._operation_locks:
            del self._operation_locks[operation_id]
            logging.debug(f"Cleaned up locks for operation {operation_id}")

# Global atomic state manager instance
_atomic_state_manager = AtomicStateManager()

def get_atomic_state_manager() -> AtomicStateManager:
    """Get the global atomic state manager instance"""
    return _atomic_state_manager

def atomic_state_update(key: str, update_function: Callable[[Any], Any], default_value: Any = None):
    """Convenience function for atomic state update"""
    manager = get_atomic_state_manager()
    return manager.atomic_state_update(key, update_function, default_value)

def atomic_batch_update(updates: Dict[str, Callable[[Any], Any]], defaults: Optional[Dict[str, Any]] = None):
    """Convenience function for atomic batch update"""
    manager = get_atomic_state_manager()
    return manager.atomic_batch_update(updates, defaults)

def atomic_operation(operation_id: str, operation_function: Callable, *args, **kwargs):
    """Convenience function for atomic operation"""
    manager = get_atomic_state_manager()
    return manager.atomic_operation(operation_id, operation_function, *args, **kwargs)

def safe_state_reset(keys: List[str], reset_values: Optional[Dict[str, Any]] = None):
    """Convenience function for safe state reset"""
    manager = get_atomic_state_manager()
    return manager.safe_state_reset(keys, reset_values)

@contextmanager
def atomic_processing_state(operation_id: str, processing_keys: List[str]):
    """
    Context manager for atomic processing state management
    
    Args:
        operation_id: Unique operation identifier
        processing_keys: List of processing state keys to manage
    """
    manager = get_atomic_state_manager()
    
    try:
        # Set processing state atomically
        processing_updates = {key: lambda x: True for key in processing_keys}
        manager.atomic_batch_update(processing_updates)
        
        yield manager
        
    except Exception as e:
        # Reset processing state on error
        manager.safe_state_reset(processing_keys, {key: False for key in processing_keys})
        raise
        
    finally:
        # Reset processing state
        manager.safe_state_reset(processing_keys, {key: False for key in processing_keys})
        
        # Clean up operation locks
        manager.cleanup_operation_locks(operation_id)
