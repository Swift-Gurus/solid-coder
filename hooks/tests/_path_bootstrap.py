"""
solid-description: Re-exports ensure_on_path from the canonical hook_utils definition for use in hook test suites.
solid-category: unit-test
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import ensure_on_path  # noqa: E402, F401  # re-export
