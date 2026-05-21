"""
solid-description: Shared pytest configuration that makes hook modules importable across all hook test files without per-file path setup.
solid-category: unit-test
"""

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("_path_bootstrap", _HERE / "_path_bootstrap.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_mod.ensure_on_path(_HERE.parent, _HERE)
