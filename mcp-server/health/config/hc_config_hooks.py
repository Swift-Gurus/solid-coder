"""
solid-description: Returns exclusion patterns for a named hook.
solid-category: utility
solid-tags: [hook]
"""

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hc_config_core import read_section  # noqa: E402


def hook_exclude_patterns(hook: str) -> list:
    """Return the exclude glob patterns for a named hook.

    Reads [hooks.<hook>].exclude from the project config, e.g.:

        [hooks.pre_write_gate]
        exclude = ["tests/fixtures/**"]

    Returns an empty list when the section or key is absent.
    """
    return list(read_section("hooks").get(hook, {}).get("exclude", []))
