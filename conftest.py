"""Pytest bootstrap: make repo-root modules importable regardless of how
pytest is invoked (`pytest`, `python -m pytest`, from another cwd, etc.).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
