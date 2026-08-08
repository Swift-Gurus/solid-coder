"""Applies a turn-counted event to reconstructed state."""


"""
solid-name: TurnCountedTransition
solid-category: service
solid-spec: [SPEC-030]
solid-description: Advances reconstructed run turn count from an explicit total or one incremental turn.
"""
class TurnCountedTransition:
    def apply(self, state: dict, event: dict) -> None:
        state["turn_count"] = event.get("total", state["turn_count"] + 1)
