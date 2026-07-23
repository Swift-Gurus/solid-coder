"""
solid-name: StepHandlerResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving handlers for step types.
"""

from __future__ import annotations

from typing import Protocol

from harness.step_handling import StepHandling


class StepHandlerResolving(Protocol):

    def resolve(self, step_type: str) -> StepHandling: ...
