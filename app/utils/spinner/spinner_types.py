"""
Spinner Types and Configuration

This module defines the types of spinners and their configuration options.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any, List
from contextlib import contextmanager
import streamlit as st
import logging

class SpinnerType(Enum):
    """Enumeration of spinner types for different operations."""
    SAVE = "save"
    DELETE = "delete"
    AI_PROCESSING = "ai_processing"
    DATABASE = "database"
    UI_REFRESH = "ui_refresh"
    ANALYSIS = "analysis"
    SEARCH = "search"
    GENERATE = "generate"
    LOAD = "load"
    PROCESS = "process"

@dataclass
class SpinnerConfig:
    """Configuration for a spinner operation."""
    type: SpinnerType
    message: str
    icon: str = "🔄"
    show_progress: bool = False
    progress_callback: Optional[Callable] = None
    timeout_seconds: Optional[int] = None
    show_toast_on_complete: bool = True
    toast_success_message: Optional[str] = None
    toast_error_message: Optional[str] = None
    log_operation: bool = True
    custom_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SpinnerContext:
    """Context information for a spinner operation."""
    config: SpinnerConfig
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    operation_data: Dict[str, Any] = field(default_factory=dict)

class SpinnerPresets:
    """Predefined spinner configurations for common operations."""
    
    @staticmethod
    def save_components(count: int = 0) -> SpinnerConfig:
        """Spinner for saving value components."""
        message = f"Saving {count} components" if count > 0 else "Saving components"
        return SpinnerConfig(
            type=SpinnerType.SAVE,
            message=message,
            icon="💾",
            show_toast_on_complete=True,
            toast_success_message="✅ Components saved successfully!",
            toast_error_message="❌ Failed to save components"
        )
    
    @staticmethod
    def delete_operation(item_type: str = "item") -> SpinnerConfig:
        """Spinner for delete operations."""
        return SpinnerConfig(
            type=SpinnerType.DELETE,
            message=f"🗑️ Deleting {item_type}...",
            icon="🗑️",
            show_toast_on_complete=True,
            toast_success_message=f"✅ {item_type.title()} deleted successfully!",
            toast_error_message=f"❌ Failed to delete {item_type}"
        )
    
    @staticmethod
    def ai_processing(operation: str, count: int = 0) -> SpinnerConfig:
        """Spinner for AI processing operations."""
        message = f"🤖 {operation}"
        if count > 0:
            message += f" for {count} items"
        return SpinnerConfig(
            type=SpinnerType.AI_PROCESSING,
            message=message,
            icon="🤖",
            timeout_seconds=120,  # 2 minutes timeout for AI operations
            show_toast_on_complete=True,
            toast_success_message=f"✅ AI processing completed successfully!",
            toast_error_message="❌ AI processing failed"
        )
    
    @staticmethod
    def database_operation(operation: str, count: int = 0) -> SpinnerConfig:
        """Spinner for database operations."""
        message = f"💾 {operation}"
        if count > 0:
            message += f" {count} items"
        return SpinnerConfig(
            type=SpinnerType.DATABASE,
            message=message,
            icon="💾",
            show_toast_on_complete=False  # Database ops are usually part of larger operations
        )
    
    @staticmethod
    def ui_refresh() -> SpinnerConfig:
        """Spinner for UI refresh operations."""
        return SpinnerConfig(
            type=SpinnerType.UI_REFRESH,
            message="🔄 Refreshing UI with latest data...",
            icon="🔄",
            show_toast_on_complete=False
        )
    
    @staticmethod
    def analysis(operation: str) -> SpinnerConfig:
        """Spinner for analysis operations."""
        return SpinnerConfig(
            type=SpinnerType.ANALYSIS,
            message=f"🔍 {operation}",
            icon="🔍",
            show_toast_on_complete=True,
            toast_success_message="✅ Analysis completed successfully!",
            toast_error_message="❌ Analysis failed"
        )
    
    @staticmethod
    def search(query_type: str = "data") -> SpinnerConfig:
        """Spinner for search operations."""
        return SpinnerConfig(
            type=SpinnerType.SEARCH,
            message=f"🔍 Searching {query_type}...",
            icon="🔍",
            timeout_seconds=30,
            show_toast_on_complete=False
        )
    
    @staticmethod
    def generate(item_type: str) -> SpinnerConfig:
        """Spinner for generation operations."""
        return SpinnerConfig(
            type=SpinnerType.GENERATE,
            message=f"✨ Generating {item_type}...",
            icon="✨",
            timeout_seconds=180,  # 3 minutes for generation
            show_toast_on_complete=True,
            toast_success_message=f"✅ {item_type.title()} generated successfully!",
            toast_error_message=f"❌ Failed to generate {item_type}"
        ) 