#!/usr/bin/env python3
"""
solid-description: Service that validates solid-coder configuration and gates tool operations.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[1]
_MCP_HEALTH = _MCP_DIR / "health"
for _d in (
    _MCP_DIR,
    _MCP_DIR / "gate",
    _MCP_DIR / "patch",
    _MCP_DIR / "output",
    _MCP_DIR / "utils",
    _MCP_DIR / "session",
    _MCP_HEALTH,
    _MCP_HEALTH / "config",
    _MCP_HEALTH / "llm",
    _MCP_HEALTH / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from default_coordinator_factory import DefaultCoordinatorFactory
from hook_utils import HookGateFactory
from solid_coder_config_error import SolidCoderConfigError

_GATE = HookGateFactory().build()
_ORCHESTRATOR = DefaultCoordinatorFactory().make_orchestrator(_GATE)


def main() -> None:
    try:
        _ORCHESTRATOR.run(sys.stdin.read())
    except SolidCoderConfigError as exc:
        _GATE.block(
            "solid-coder config invalid — fix .solid-coder/config.toml or config.local.toml",
            additional_context=str(exc),
        )


if __name__ == "__main__":
    main()
