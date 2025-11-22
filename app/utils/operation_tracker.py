"""
Operation Tracker

This module provides comprehensive operation tracking and monitoring
to ensure operations are properly managed and can be debugged.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
import streamlit as st
from dataclasses import dataclass, asdict
from enum import Enum

class OperationStatus(Enum):
    """Status of an operation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class OperationInfo:
    """Information about an operation"""
    operation_id: str
    operation_type: str
    status: OperationStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def is_active(self) -> bool:
        """Check if operation is currently active"""
        return self.status in [OperationStatus.PENDING, OperationStatus.RUNNING]
    
    def is_finished(self) -> bool:
        """Check if operation is finished"""
        return self.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, 
                              OperationStatus.CANCELLED, OperationStatus.TIMEOUT]
    
    def calculate_duration(self) -> float:
        """Calculate operation duration"""
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0.0

class OperationTracker:
    """Tracks operations and their status"""
    
    def __init__(self):
        self.operations: Dict[str, OperationInfo] = {}
        self.operation_history: List[OperationInfo] = []
        self.max_history = 100  # Keep last 100 operations
    
    def start_operation(self, operation_id: str, operation_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Start tracking an operation"""
        try:
            if operation_id in self.operations:
                logging.warning(f"Operation {operation_id} already exists, updating")
                self.update_operation_status(operation_id, OperationStatus.RUNNING)
                return True
            
            operation_info = OperationInfo(
                operation_id=operation_id,
                operation_type=operation_type,
                status=OperationStatus.PENDING,
                start_time=time.time(),
                metadata=metadata or {}
            )
            
            self.operations[operation_id] = operation_info
            logging.info(f"Started tracking operation {operation_id} of type {operation_type}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start tracking operation {operation_id}: {e}")
            return False
    
    def update_operation_status(self, operation_id: str, status: OperationStatus, error_message: Optional[str] = None) -> bool:
        """Update the status of an operation"""
        try:
            if operation_id not in self.operations:
                logging.warning(f"Operation {operation_id} not found")
                return False
            
            operation = self.operations[operation_id]
            operation.status = status
            
            if status in [OperationStatus.COMPLETED, OperationStatus.FAILED, 
                         OperationStatus.CANCELLED, OperationStatus.TIMEOUT]:
                operation.end_time = time.time()
                operation.duration = operation.calculate_duration()
                
                if error_message:
                    operation.error_message = error_message
                
                # Move to history - keep as OperationInfo object
                self.operation_history.append(operation)
                if len(self.operation_history) > self.max_history:
                    self.operation_history.pop(0)
                
                # Remove from active operations
                del self.operations[operation_id]
                
                logging.info(f"Operation {operation_id} finished with status {status.value}")
            else:
                logging.debug(f"Operation {operation_id} status updated to {status.value}")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to update operation {operation_id} status: {e}")
            return False
    
    def get_operation(self, operation_id: str) -> Optional[OperationInfo]:
        """Get information about an operation"""
        return self.operations.get(operation_id)
    
    def get_active_operations(self) -> List[OperationInfo]:
        """Get all active operations"""
        return [op for op in self.operations.values() if op.is_active()]
    
    def get_operation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent operation history"""
        return [op.to_dict() for op in self.operation_history[-limit:]]
    
    def get_operations_by_type(self, operation_type: str) -> List[OperationInfo]:
        """Get operations by type"""
        return [op for op in self.operations.values() if op.operation_type == operation_type]
    
    def get_long_running_operations(self, threshold_seconds: float = 60) -> List[OperationInfo]:
        """Get operations that have been running for too long"""
        current_time = time.time()
        return [
            op for op in self.operations.values()
            if op.is_active() and (current_time - op.start_time) > threshold_seconds
        ]
    
    def cleanup_old_operations(self, max_age_seconds: float = 3600) -> int:
        """Clean up old operations"""
        current_time = time.time()
        to_remove = []
        
        for operation_id, operation in self.operations.items():
            if operation.is_finished() and (current_time - operation.start_time) > max_age_seconds:
                to_remove.append(operation_id)
        
        for operation_id in to_remove:
            del self.operations[operation_id]
        
        logging.info(f"Cleaned up {len(to_remove)} old operations")
        return len(to_remove)
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get statistics about operations"""
        active_ops = self.get_active_operations()
        history_ops = self.operation_history
        
        stats = {
            "active_operations": len(active_ops),
            "total_operations": len(self.operations) + len(history_ops),
            "recent_operations": len(history_ops),
            "operation_types": {},
            "status_counts": {},
            "average_duration": 0.0,
            "long_running_operations": len(self.get_long_running_operations())
        }
        
        # Count by type
        for op in list(self.operations.values()) + history_ops:
            op_type = op.operation_type
            stats["operation_types"][op_type] = stats["operation_types"].get(op_type, 0) + 1
            
            # Count by status
            status = op.status.value
            stats["status_counts"][status] = stats["status_counts"].get(status, 0) + 1
        
        # Calculate average duration
        durations = [op.duration for op in history_ops if op.duration is not None]
        if durations:
            stats["average_duration"] = sum(durations) / len(durations)
        
        return stats
    
    def export_operation_log(self) -> Dict[str, Any]:
        """Export operation log for debugging"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_operations": [op.to_dict() for op in self.operations.values()],
            "operation_history": self.operation_history,
            "stats": self.get_operation_stats()
        }

# Global operation tracker instance
_operation_tracker = OperationTracker()

def get_operation_tracker() -> OperationTracker:
    """Get the global operation tracker instance"""
    return _operation_tracker

def track_operation(operation_id: str, operation_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience function to start tracking an operation"""
    tracker = get_operation_tracker()
    return tracker.start_operation(operation_id, operation_type, metadata)

def update_operation_status(operation_id: str, status: OperationStatus, error_message: Optional[str] = None) -> bool:
    """Convenience function to update operation status"""
    tracker = get_operation_tracker()
    return tracker.update_operation_status(operation_id, status, error_message)

def get_active_operations() -> List[OperationInfo]:
    """Convenience function to get active operations"""
    tracker = get_operation_tracker()
    return tracker.get_active_operations()

def get_operation_stats() -> Dict[str, Any]:
    """Convenience function to get operation statistics"""
    tracker = get_operation_tracker()
    return tracker.get_operation_stats()

def cleanup_old_operations(max_age_seconds: float = 3600) -> int:
    """Convenience function to cleanup old operations"""
    tracker = get_operation_tracker()
    return tracker.cleanup_old_operations(max_age_seconds)

def get_long_running_operations(threshold_seconds: float = 60) -> List[OperationInfo]:
    """Convenience function to get long running operations"""
    tracker = get_operation_tracker()
    return tracker.get_long_running_operations(threshold_seconds)
