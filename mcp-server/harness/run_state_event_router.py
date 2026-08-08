"""Routes workflow events by their declared event name."""

from __future__ import annotations

from harness.run_state_transitioning import RunStateTransitioning


"""
solid-name: RunStateEventRouter
solid-category: service
solid-spec: [SPEC-030]
solid-description: Routes recognized workflow events to injected run-state transitions.
"""
class RunStateEventRouter:

    def __init__(self, transitions: dict[str, RunStateTransitioning]) -> None:
        self._transitions = transitions

    def route(self, state: dict, event: dict) -> None:
        transition = self._transitions.get(event.get("event"))
        if transition is not None:
            transition.apply(state, event)
