"""
solid-description: Executes plugin skills as subprocesses and formats their execution results.
solid-category: service
solid-tags: [utility, service]
"""

import sys
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, Tuple

from lib.subprocess_utils import run_cmd as _default_run_cmd

CommandRunning = Callable[[list], Tuple[bool, str, str]]


class SkillRunning(Protocol):
    def execute(self, skill_dir: str, script_name: str, args: list) -> Tuple[bool, str, str]: ...


class ResultFormatting(Protocol):
    def format(self, ok: bool, err: str, **fields: Any) -> dict: ...


class SkillRunner:
    """Executes plugin skill scripts and returns (ok, stdout, stderr)."""

    def __init__(
        self,
        skills_root: Path,
        python: Optional[str] = None,
        cmd_runner: Optional[CommandRunning] = None,
    ) -> None:
        self._skills_root = skills_root
        self._python = python or sys.executable
        self._cmd_runner = cmd_runner or _default_run_cmd

    def execute(self, skill_dir: str, script_name: str, args: list) -> Tuple[bool, str, str]:
        """Run a skill script and return (ok, stdout, stderr)."""
        path = str(self._skills_root / skill_dir / "scripts" / script_name)
        return self._cmd_runner([self._python, path] + args)


class SkillResultFormatter:
    """Formats skill execution outcomes into uniform result dicts."""

    def format(self, ok: bool, err: str, **fields: Any) -> dict:
        """Build a result dict. Error field is populated only on failure."""
        return {**fields, "error": err if not ok else None}
