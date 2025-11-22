#!/usr/bin/env python3
"""
Launcher for Authenticated Value Rollercoaster Application
Run this script to start the authenticated version of the app.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import and run the authenticated app
from app.ui_auth import AuthenticatedUI

def main():
    """Main entry point for the authenticated app."""
    ui = AuthenticatedUI()
    ui.run()

if __name__ == "__main__":
    main() 