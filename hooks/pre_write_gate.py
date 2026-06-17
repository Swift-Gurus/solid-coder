#!/usr/bin/env python3
"""
solid-description: PreToolUse gate entry point — routes Write, Edit, and apply_patch events through the health check and frontmatter pipeline.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from default_coordinator_factory import DefaultCoordinatorFactory
from hook_utils import HookGateFactory

_GATE = HookGateFactory().build()
_ORCHESTRATOR = DefaultCoordinatorFactory().make_orchestrator(_GATE)


def main() -> None:
    _ORCHESTRATOR.run(sys.stdin.read())


if __name__ == "__main__":
    main()
