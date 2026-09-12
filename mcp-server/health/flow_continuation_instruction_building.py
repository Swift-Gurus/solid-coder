"""Defines flow-continuation guidance for an isolated model backend."""

from typing import Protocol


"""
solid-name: FlowContinuationInstructionBuilding
solid-category: abstraction
solid-spec: [SPEC-047]
solid-description: Contract for rendering directly callable flow-continuation guidance for one model backend.
"""
class FlowContinuationInstructionBuilding(Protocol):
    def build(self, run_id: str) -> str: ...
