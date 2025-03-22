"""
This module disables the creation of __pycache__ directories and .pyc files.
Import this module at the start of the application to prevent Python from
creating these files.
"""
import sys

# Set the PYTHONDONTWRITEBYTECODE environment variable
sys.dont_write_bytecode = True

def disable_pycache():
    """Disable the creation of __pycache__ directories and .pyc files."""
    sys.dont_write_bytecode = True
    print("Python bytecode generation disabled (__pycache__ and .pyc files will not be created)")