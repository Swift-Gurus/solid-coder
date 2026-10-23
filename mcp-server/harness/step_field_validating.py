"""Defines workflow-step field validation."""

from __future__ import annotations

from typing import Protocol, TypeVar

_StepFields_contra = TypeVar("_StepFields_contra", contravariant=True)


"""
solid-name: StepFieldValidating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for validating the fields exposed by a workflow-step role.
"""


class StepFieldValidating(Protocol[_StepFields_contra]):
    def validate(self, step: _StepFields_contra) -> None: ...
