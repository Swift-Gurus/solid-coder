"""
solid-description: Evaluates stop events and determines whether to allow or block the requested action.
solid-category: hook
"""

import sys
from pathlib import Path
from typing import Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
_MCP_HEALTH = _MCP_DIR / "health"
for _d in (_MCP_DIR, _MCP_HEALTH, _MCP_HEALTH / "config"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_decision import HookDecision
from hook_responding import HookResponding
from hook_utils import ensure_on_path, parse_json_safely
from logging_protocol import Logging
from stderr_logger import StderrLogger


class StopEventReading(Protocol):
    """Narrow read protocol for the Stop event source."""

    def read(self) -> dict: ...


class HookDispatching(Protocol):
    """Narrow dispatch protocol for a Stop event gate."""

    def dispatch(self, event: dict) -> HookDecision: ...


class EventSource(Protocol):
    """Protocol for reading raw event text."""

    def read(self) -> str: ...


_DEFAULT_LOGGER: Logging = StderrLogger()


class HookEventReader:
    """Reads and parses a Claude Code Stop event from an injectable source."""

    def __init__(
        self, source: EventSource | None = None, logger: Logging = _DEFAULT_LOGGER
    ) -> None:
        self._source = source  # None means use sys.stdin at call time
        self._logger = logger

    def read(self) -> dict:
        raw = self._source.read() if self._source is not None else sys.stdin.read()
        if not raw.strip():
            return {}
        parsed = parse_json_safely(raw)
        if parsed is None:
            self._logger.log("on_stop: failed to parse Stop event: invalid JSON")
            return {}
        return parsed


def main(
    reader: StopEventReading, dispatcher: HookDispatching, responder: HookResponding
) -> None:
    """Dispatch a Stop event, then render the aggregated decision via the responder."""
    event = reader.read()
    decision = dispatcher.dispatch(event)
    if not decision.allow:
        responder.block(
            decision.reason or "Blocked.", decision.additional_context or ""
        )
    else:
        responder.allow(decision.additional_context or "")


if __name__ == "__main__":
    ensure_on_path(Path(__file__).resolve().parent)
    from concurrent_handler_executor import ConcurrentHandlerExecutor
    from flow_transition_gate_factory import FlowTransitionGateFactory
    from flow_transition_handler import FlowStopEvaluator, FlowTransitionHandler
    from parallel_hook_dispatcher import ParallelHookDispatcher
    from pre_read_event_reader import PreReadEventReader
    from session_validation_handler import SessionValidationHandler
    from slack_notify import SlackStopNotifier
    from slack_stop_handler import SlackStopHandler
    from stop_hook_responder import StopHookResponder

    stop_event = HookEventReader().read()
    stop_session_id = stop_event.get("session_id", "")

    main(
        reader=PreReadEventReader(stop_event),
        dispatcher=ParallelHookDispatcher(
            executor=ConcurrentHandlerExecutor(
                handlers=[
                    SlackStopHandler(SlackStopNotifier()),
                    SessionValidationHandler(),
                    FlowTransitionHandler(
                        evaluator=FlowStopEvaluator(
                            FlowTransitionGateFactory(
                                session_id=stop_session_id
                            ).build()
                        )
                    ),
                ]
            )
        ),
        responder=StopHookResponder(),
    )
