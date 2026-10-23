"""
solid-description: Provides hook scripts an interface for logging and controlling hook execution outcomes.
solid-category: service
solid-tags: [hook]
"""

from gate.hook_context_buffer import HookContextBuffering
from hook_responding import HookResponding
from logging_protocol import Logging

"""
solid-name: HookGate
solid-category: service
solid-tags: [hook]
solid-description: Provides hook diagnostics, retained warning context, and allow-or-block responses.
"""


class HookGate:
    """Pure Facade composing Logging and HookResponding for hook scripts.

    All dependencies are protocol-typed and injected via __init__. Use
    HookGateFactory to wire production defaults.
    """

    def __init__(
        self, logger: Logging, responder: HookResponding, context: HookContextBuffering
    ) -> None:
        self._logger = logger
        self._responder = responder
        self._context = context

    def log(self, msg: str) -> None:
        return self._logger.log(msg)

    def warn(self, message: str) -> None:
        self._context.append(message)

    def allow(
        self, additional_context: str = "", updated_input: dict | None = None
    ) -> None:
        return self._responder.allow(
            self._context.consume(additional_context), updated_input
        )

    def block(self, reason: str, additional_context: str = "") -> None:
        return self._responder.block(reason, self._context.consume(additional_context))
