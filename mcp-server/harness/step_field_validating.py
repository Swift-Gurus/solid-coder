"""Defines workflow-step field validation."""

from __future__ import annotations

from typing import Protocol, TypeVar

_StepFields = TypeVar("_StepFields", contravariant=True)


"""
solid-name: StepFieldValidating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for validating the fields exposed by a workflow-step role.
"""
class StepFieldValidating(Protocol[_StepFields]):
    def validate(self, step: _StepFields) -> None: ...
