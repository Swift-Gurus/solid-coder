"""Defines validation of workflow for-each references."""

from __future__ import annotations

from typing import Protocol

from harness.models import StepDef


"""
solid-name: ForEachReferenceValidating
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for validating workflow for-each source outputs and dependency reachability.
"""
class ForEachReferenceValidating(Protocol):
    def validate_for_each_references(self, steps: list[StepDef]) -> None: ...
