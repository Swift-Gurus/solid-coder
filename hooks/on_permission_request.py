#!/usr/bin/env python3
"""
solid-description: Sends a Slack notification when tool permission is requested.
solid-category: hook

Fires on every PermissionRequest event. Sends a one-way notification so the user
knows Claude is waiting for approval. Does not make a decision — exits 0 without
output so the normal permission prompt proceeds unchanged.
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_MCP_HEALTH_CONFIG = _HOOKS_DIR.parent / "mcp-server" / "health" / "config"
for _d in (_HOOKS_DIR, _MCP_HEALTH_CONFIG):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import ensure_on_path  # noqa: E402
from on_stop import HookEventReader, OnStopGate, main  # noqa: E402
from slack_notify import SlackPermissionNotifier  # noqa: E402

if __name__ == "__main__":
    ensure_on_path(Path(__file__).resolve().parent)
    main(
        reader=HookEventReader(),
        gate=OnStopGate(handlers=[SlackPermissionNotifier()]),
    )