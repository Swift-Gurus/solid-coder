"""
solid-name: _path_bootstrap
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Ensures harness and hooks directories are available on sys.path for test imports.
Re-exports ensure_on_path from the canonical hooks/tests/_path_bootstrap to avoid duplication.
"""

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HOOKS_TESTS = _PROJECT_ROOT / "hooks" / "tests"

_spec = importlib.util.spec_from_file_location(
    "_hooks_path_bootstrap", _HOOKS_TESTS / "_path_bootstrap.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

ensure_on_path = _mod.ensure_on_path
