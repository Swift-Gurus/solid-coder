"""Defines workflow-step declaration mapping."""

from __future__ import annotations

from typing import Protocol

from harness.step_declaration import StepDeclaration


"""
solid-name: StepDeclarationMapping
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for transforming raw workflow-step input into an unvalidated declaration.
"""
class StepDeclarationMapping(Protocol):
    def map(self, raw: dict) -> StepDeclaration: ...
