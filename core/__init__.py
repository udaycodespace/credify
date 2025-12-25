# core/__init__.py
import os
from pathlib import Path

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Export for use in other core modules
__all__ = ['PROJECT_ROOT', 'DATA_DIR']
