#!/usr/bin/env python3
"""
solid-description: PreToolUse gate entry point — routes Write, Edit, and apply_patch events through the health check and frontmatter pipeline.
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

_GATE = HookGateFactory().build()
_ORCHESTRATOR = DefaultCoordinatorFactory().make_orchestrator(_GATE)


def main() -> None:
    _ORCHESTRATOR.run(sys.stdin.read())


if __name__ == "__main__":
    main()
