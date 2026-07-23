"""
solid-name: CommandAllowlistResolver
solid-category: service
solid-spec: [SPEC-027]
solid-description: Resolves the executables permitted for script execution.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

_HEALTH_CONFIG_DIR = Path(__file__).resolve().parents[1] / "health" / "config"
if str(_HEALTH_CONFIG_DIR) not in sys.path:
    sys.path.insert(0, str(_HEALTH_CONFIG_DIR))

from harness.command_allowlist_resolving import CommandAllowlistResolving
from hc_config_core import read_section  # noqa: E402


class CommandAllowlistResolver(CommandAllowlistResolving):

    def __init__(self, section_reader: Callable[[str], dict] = read_section) -> None:
        self._section_reader = section_reader

    def resolve(self) -> list[str]:
        return self._section_reader("flow_engine").get("permitted_executables", [])
