"""
solid-name: SafeHandlerRunner
solid-category: service
solid-description: Safely executes a hook handler without propagating exceptions.
solid-tags: [hook]
"""

from hook_decision import HookDecision
from hook_handling import HookHandling
from logging_protocol import Logging
from stderr_logger import StderrLogger


class SafeHandlerRunner:
    def __init__(self, logger: Logging = StderrLogger()) -> None:
        self._logger = logger

    def run(self, handler: HookHandling, event: dict) -> HookDecision:
        try:
            return handler.handle(event)
        except Exception as exc:
            self._logger.log(f"hook handler {handler!r} raised: {exc}")
            return HookDecision(allow=True)
