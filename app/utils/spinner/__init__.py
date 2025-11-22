"""
Spinner Utility Module

This module provides centralized spinner management for the ValueRollerCoaster application.
It offers consistent loading states, progress tracking, and error handling across all components.

Usage:
    from app.utils.spinner import SpinnerManager, SpinnerConfig, SpinnerType
    
    spinner_mgr = SpinnerManager()
    config = SpinnerConfig(
        type=SpinnerType.SAVE,
        message="Saving components",
        icon="💾"
    )
    
    with spinner_mgr.spinner(config):
        # Your operation here
        pass
"""

from .spinner_types import SpinnerType, SpinnerConfig, SpinnerContext
from .spinner_manager import SpinnerManager
from .progress_tracker import ProgressTracker, MultiStepProgress
from .spinner_contexts import (
    save_spinner,
    delete_spinner,
    ai_processing_spinner,
    database_spinner,
    ui_refresh_spinner,
    analysis_spinner,
    search_spinner,
    generate_spinner,
    dialog_spinner,
    multi_step_save_spinner,
    custom_spinner
)

__all__ = [
    "SpinnerType",
    "SpinnerConfig", 
    "SpinnerContext",
    "SpinnerManager",
    "ProgressTracker",
    "MultiStepProgress",
    "save_spinner",
    "delete_spinner", 
    "ai_processing_spinner",
    "database_spinner",
    "ui_refresh_spinner",
    "analysis_spinner",
    "search_spinner",
    "generate_spinner",
    "dialog_spinner",
    "multi_step_save_spinner",
    "custom_spinner"
] 