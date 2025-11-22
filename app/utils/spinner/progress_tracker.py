"""
Progress Tracking for Spinner Operations

This module provides progress tracking capabilities for multi-step operations
and long-running processes.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from contextlib import contextmanager
import streamlit as st
import logging

@dataclass
class ProgressStep:
    """Represents a single step in a multi-step operation."""
    name: str
    description: str
    weight: float = 1.0  # Relative weight of this step
    completed: bool = False
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)

class ProgressTracker:
    """Tracks progress for a single operation."""
    
    def __init__(self, total_steps: int = 1, operation_name: str = "Operation"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.steps: List[ProgressStep] = []
        self.logger = logging.getLogger(__name__)
        
    def update(self, step_name: str, progress: Optional[float] = None, description: Optional[str] = None):
        """Update progress with optional custom progress value."""
        if progress is not None:
            self.current_step = int(progress * self.total_steps)
        
        if description:
            self.logger.info(f"[{self.operation_name}] {step_name}: {description}")
        else:
            self.logger.info(f"[{self.operation_name}] {step_name}")
    
    def next_step(self, step_name: str, description: Optional[str] = None):
        """Move to next step automatically."""
        self.current_step += 1
        self.update(step_name, description=description)
    
    def complete(self):
        """Mark the operation as complete."""
        self.end_time = time.time()
        self.current_step = self.total_steps
        self.logger.info(f"[{self.operation_name}] Completed in {self.duration:.2f}s")
    
    @property
    def duration(self) -> float:
        """Get the duration of the operation."""
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    @property
    def progress_percentage(self) -> float:
        """Get the current progress as a percentage."""
        if self.total_steps <= 0:
            return 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100)

class MultiStepProgress:
    """Manages progress for multi-step operations with detailed tracking."""
    
    def __init__(self, operation_name: str = "Multi-step Operation"):
        self.operation_name = operation_name
        self.steps: List[ProgressStep] = []
        self.current_step_index = -1
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.logger = logging.getLogger(__name__)
    
    def add_step(self, name: str, description: str, weight: float = 1.0) -> int:
        """Add a step to the operation."""
        step = ProgressStep(name=name, description=description, weight=weight)
        self.steps.append(step)
        return len(self.steps) - 1
    
    @contextmanager
    def step(self, name: str, description: Optional[str] = None, weight: float = 1.0):
        """Context manager for a single step."""
        step_index = self.add_step(name, description or name, weight)
        self.start_step(step_index)
        
        try:
            yield self
            self.complete_step(step_index)
        except Exception as e:
            self.fail_step(step_index, str(e))
            raise
    
    def start_step(self, step_index: int):
        """Start a specific step."""
        if 0 <= step_index < len(self.steps):
            self.current_step_index = step_index
            step = self.steps[step_index]
            step.start_time = time.time()
            step.completed = False
            step.error = None
            
            self.logger.info(f"[{self.operation_name}] Starting step {step_index + 1}/{len(self.steps)}: {step.name}")
    
    def complete_step(self, step_index: int):
        """Complete a specific step."""
        if 0 <= step_index < len(self.steps):
            step = self.steps[step_index]
            step.end_time = time.time()
            step.completed = True
            
            duration = step.end_time - step.start_time if step.start_time else 0
            self.logger.info(f"[{self.operation_name}] Completed step {step_index + 1}/{len(self.steps)}: {step.name} ({duration:.2f}s)")
    
    def fail_step(self, step_index: int, error_message: str):
        """Mark a step as failed."""
        if 0 <= step_index < len(self.steps):
            step = self.steps[step_index]
            step.end_time = time.time()
            step.completed = False
            step.error = error_message
            
            duration = step.end_time - step.start_time if step.start_time else 0
            self.logger.error(f"[{self.operation_name}] Failed step {step_index + 1}/{len(self.steps)}: {step.name} ({duration:.2f}s) - {error_message}")
    
    def complete(self):
        """Mark the entire operation as complete."""
        self.end_time = time.time()
        self.logger.info(f"[{self.operation_name}] All steps completed in {self.duration:.2f}s")
    
    @property
    def duration(self) -> float:
        """Get the total duration of the operation."""
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    @property
    def progress_percentage(self) -> float:
        """Get the current progress as a percentage based on completed steps."""
        if not self.steps:
            return 0.0
        
        total_weight = sum(step.weight for step in self.steps)
        if total_weight <= 0:
            return 0.0
        
        completed_weight = sum(step.weight for step in self.steps if step.completed)
        return min(100.0, (completed_weight / total_weight) * 100)
    
    @property
    def current_step_name(self) -> Optional[str]:
        """Get the name of the current step."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index].name
        return None
    
    @property
    def completed_steps(self) -> int:
        """Get the number of completed steps."""
        return sum(1 for step in self.steps if step.completed)
    
    @property
    def total_steps(self) -> int:
        """Get the total number of steps."""
        return len(self.steps)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the operation."""
        return {
            "operation_name": self.operation_name,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "progress_percentage": self.progress_percentage,
            "duration": self.duration,
            "current_step": self.current_step_name,
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "completed": step.completed,
                    "error": step.error,
                    "duration": step.end_time - step.start_time if step.start_time and step.end_time else None
                }
                for step in self.steps
            ]
        }

class StreamlitProgressBar:
    """Streamlit-specific progress bar wrapper."""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self.progress_bar = None
    
    def update(self, step_name: str, progress: Optional[float] = None):
        """Update progress with Streamlit progress bar."""
        if progress is not None:
            self.progress_tracker.update(step_name, progress)
            if self.progress_bar is None:
                self.progress_bar = st.progress(0)
            
            self.progress_bar.progress(progress)
            st.write(f"**{step_name}**")
        else:
            self.progress_tracker.update(step_name)
            st.write(f"**{step_name}**")
    
    def complete(self):
        """Mark progress as complete."""
        self.progress_tracker.complete()
        if self.progress_bar:
            self.progress_bar.progress(1.0)
            st.success("✅ Operation completed!") 