"""Coordinates reconstruction of run state from persisted events."""

from __future__ import annotations

from harness.run_state import RunState
from harness.run_state_building import RunStateBuilding
from harness.run_state_event_routing import RunStateEventRouting


"""
solid-name: RunStateReconstructor
solid-category: service
solid-spec: [SPEC-030]
solid-description: Coordinates run-state construction by replaying events through injected transitions.
"""
class RunStateReconstructor:

    def __init__(
        self,
        state_builder: RunStateBuilding,
        event_router: RunStateEventRouting,
    ) -> None:
        self._state_builder = state_builder
        self._event_router = event_router

    def reconstruct(self, events: list[dict]) -> RunState:
        state = self._state_builder.empty()
        for event in events:
            self._event_router.route(state, event)
        return self._state_builder.finish(state)
