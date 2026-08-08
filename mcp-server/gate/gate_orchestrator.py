"""Coordinates the pre-write gate workflow."""

from gate_handling import GateHandling
from gate_request_routing import GateRequestRouting
from guard_checking import GuardChecking
from hook_event_parsing import HookEventParsing


"""
solid-name: GateOrchestrator
solid-description: Coordinates gate availability, event parsing, and request routing.
solid-category: service
solid-tags: [hook]
"""
class GateOrchestrator:
    def __init__(
        self,
        gate: GateHandling,
        guard: GuardChecking,
        event_parser: HookEventParsing,
        request_router: GateRequestRouting,
    ) -> None:
        self._gate = gate
        self._guard = guard
        self._event_parser = event_parser
        self._request_router = request_router

    def run(self, raw: str) -> None:
        if not self._guard.is_available():
            self._gate.allow()
            return
        parsed = self._event_parser.parse(raw)
        if parsed is None:
            self._gate.allow()
            return
        self._request_router.route(parsed)
