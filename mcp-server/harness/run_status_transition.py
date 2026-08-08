"""Applies a terminal run status to reconstructed state."""


"""
solid-name: RunStatusTransition
solid-category: service
solid-spec: [SPEC-030, SPEC-027]
solid-description: Assigns one configured terminal status when its corresponding run event is replayed.
"""
class RunStatusTransition:

    def __init__(self, status: str) -> None:
        self._status = status

    def apply(self, state: dict, event: dict) -> None:
        state["status"] = self._status
