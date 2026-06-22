"""
solid-name: FileSystemHookContextLoader
solid-category: service
solid-description: Loads hook context from the file system.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Optional

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from hook_utils import solid_coder_project_dir  # noqa: E402
from findings.unit_coverage_validator import HookContextLoading  # noqa: E402


class FileSystemHookContextLoader(HookContextLoading):
    """Locates hook-input.json via the active-health-check pointer and reads it.

    Uses solid_coder_project_dir() for project resolution — falls back to cwd()
    when CLAUDE_PROJECT_DIR is not set, so it works in both Claude Code and Codex
    health-check sessions.

    Returns None when not in a health-check flow (no active-health-check pointer).
    """

    def __init__(self, project_dir_fn: Optional[Callable] = None) -> None:
        self._project_dir_fn = project_dir_fn or solid_coder_project_dir

    def load(self) -> Optional[dict]:
        solid_coder_dir = self._project_dir_fn()
        pointer = solid_coder_dir / "active-health-check"
        if not pointer.exists():
            return None
        health_id = pointer.read_text(encoding="utf-8").strip()
        hook_input_path = solid_coder_dir / health_id / "hook-input.json"
        if not hook_input_path.exists():
            return None
        try:
            return json.loads(hook_input_path.read_text(encoding="utf-8"))
        except Exception:
            return None
