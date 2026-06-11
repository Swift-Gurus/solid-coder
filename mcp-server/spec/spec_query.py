#!/usr/bin/env python3
"""
solid-description: Executes spec operations and returns structured results.
solid-category: utility
solid-tags: [utility, service]
"""

import json
import sys
from pathlib import Path

from common.subprocess_utils import run_cmd

_FIND_SPEC_ACTIONS = frozenset({"scan", "children", "ancestors", "next-number"})


class SpecQueryRunner:
    """Routes spec actions to the correct script and returns parsed results."""

    def __init__(self, find_spec_script: Path, build_spec_script: Path) -> None:
        self._find_spec_script = find_spec_script
        self._build_spec_script = build_spec_script

    def run(self, action: str, args: list | None = None):
        """Dispatch the action to the correct script and return the parsed result.

        Returns:
            Parsed JSON dict/list on success.
            Error string if the command fails.
            Raw stdout string if output is not valid JSON.
        """
        args = args or []
        script = (
            self._find_spec_script
            if action in _FIND_SPEC_ACTIONS
            else self._build_spec_script
        )
        ok, out, err = run_cmd([sys.executable, str(script), action] + args)
        if not ok:
            return f"Error: {err or out}"
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return out
