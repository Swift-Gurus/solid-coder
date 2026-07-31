"""
solid-description: Provides hook scripts an interface for logging and controlling hook execution outcomes.
solid-category: service
solid-tags: [hook]
"""

from typing import Optional

from hook_utils import HookResponding, Logging


class HookGate:
    """Pure Facade composing Logging and HookResponding for hook scripts.

    All dependencies are protocol-typed and injected via __init__. Use
    HookGateFactory to wire production defaults.
    """

    def __init__(self, logger: Logging, responder: HookResponding) -> None:
        self._logger = logger
        self._responder = responder

    def log(self, msg: str) -> None:
        return self._logger.log(msg)

    def allow(self, additional_context: str = "", updated_input: Optional[dict] = None) -> None:
        return self._responder.allow(additional_context, updated_input)

    def block(self, reason: str, additional_context: str = "") -> None:
        return self._responder.block(reason, additional_context)
