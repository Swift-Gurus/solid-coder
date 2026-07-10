"""
solid-description: Adapts an underlying logger to a single-message logging interface.
solid-category: utility
"""

from utils.debug_logger import DebugLogging


class GateLogger:
    """Thin wrapper: forwards a single log message onto an injected DebugLogging logger."""

    def __init__(self, logger: DebugLogging) -> None:
        self._logger = logger

    def log(self, msg: str) -> None:
        self._logger.log(msg, "")
