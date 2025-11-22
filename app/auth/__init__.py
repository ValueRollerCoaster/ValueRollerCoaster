"""
Authentication Package
Provides user management and session handling for the application.
"""

from .user_management import UserManager
from .session_manager import SessionManager

__all__ = ["UserManager", "SessionManager"] 