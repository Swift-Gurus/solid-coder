"""
solid-name: SlackStopHandler
solid-category: service
solid-description: Sends a notification as a Stop-event side effect, always permitting the event.
solid-tags: [hook]
"""

import os
import sys
from pathlib import Path
from typing import Callable, Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from hook_decision import HookDecision  # noqa: E402


class SlackNotifying(Protocol):
    def should_handle(self, event: dict) -> bool: ...

    def handle(self, event: dict) -> None: ...


class SlackStopHandler:
    """Sends a Slack notification as a side effect; never denies a Stop event.

    Internal pipeline sessions (health checks, reviews) set SOLID_CODER_SESSION_TYPE,
    which disables the notification without affecting any other handler.
    """

    def __init__(
        self,
        notifier: SlackNotifying,
        session_type_fn: Callable[[], str] = lambda: os.environ.get("SOLID_CODER_SESSION_TYPE", ""),
    ) -> None:
        self._notifier = notifier
        self._session_type_fn = session_type_fn

    def should_handle(self, event: dict) -> bool:
        if self._session_type_fn():
            return False
        return self._notifier.should_handle(event)

    def handle(self, event: dict) -> HookDecision:
        self._notifier.handle(event)
        return HookDecision(allow=True)
