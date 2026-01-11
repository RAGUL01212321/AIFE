#!/usr/bin/env python3
"""
AIFE - Advanced Interactive File Explorer
Main entry point for the application

Usage:
    python3 main.py
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui import main

if __name__ == "__main__":
    main()
