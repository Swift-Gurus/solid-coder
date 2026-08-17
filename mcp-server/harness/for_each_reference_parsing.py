"""Defines parsing of workflow for-each references."""

from __future__ import annotations

from typing import Protocol

from harness.step_output_reference import StepOutputReference


"""
solid-name: ForEachReferenceParsing
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for decoding an authored or snapshotted workflow for-each value into a typed source-output reference.
"""
class ForEachReferenceParsing(Protocol):
    def parse(self, step_id: str, expression: object) -> StepOutputReference: ...
