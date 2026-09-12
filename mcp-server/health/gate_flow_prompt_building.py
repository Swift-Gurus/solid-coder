"""Defines child-session bootstrap prompt construction."""

from typing import Protocol


"""
solid-name: GateFlowPromptBuilding
solid-category: abstraction
solid-spec: [SPEC-036]
solid-description: Contract for rendering one server-started gate flow into the child model's bootstrap prompt.
"""
class GateFlowPromptBuilding(Protocol):
    def build(
        self,
        content: str,
        path: str,
        parent_session_id: str,
        run_id: str,
        first_step: str,
    ) -> str: ...
