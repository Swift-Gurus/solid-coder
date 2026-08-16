"""Defines validation of one workflow iteration target."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef


"""
solid-name: ForEachTargetValidating
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for validating one workflow entry's iteration source.
"""
class ForEachTargetValidating(Protocol):
    def validate(
        self,
        target_id: str,
        for_each: str | None,
        dependency_ids: list[str],
        steps: list[StepDef],
    ) -> None: ...
