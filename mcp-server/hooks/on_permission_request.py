"""
solid-description: Sends a Slack notification when tool permission is requested.
solid-category: hook

Fires on every PermissionRequest event. Sends a one-way notification so the user
knows Claude is waiting for approval. Does not make a decision — exits 0 without
output so the normal permission prompt proceeds unchanged.
"""

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[1]
_MCP_HEALTH_CONFIG = _MCP_DIR / "health" / "config"
for _d in (_MCP_DIR, _MCP_HEALTH_CONFIG):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import ensure_on_path
from on_stop import HookEventReader
from slack_notify import SlackPermissionNotifier
from slack_stop_handler import SlackStopHandler

if __name__ == "__main__":
    ensure_on_path(Path(__file__).resolve().parent)
    event = HookEventReader().read()
    handler = SlackStopHandler(SlackPermissionNotifier())
    if handler.should_handle(event):
        handler.handle(event)
