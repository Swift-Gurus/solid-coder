"""Defines parsing of workflow for-each references."""

from __future__ import annotations

from typing import Protocol

from harness.for_each_reference import ForEachReference


"""
solid-name: ForEachReferenceParsing
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030]
solid-description: Contract for parsing a workflow for-each expression into a source output reference.
"""
class ForEachReferenceParsing(Protocol):
    def parse(self, step_id: str, expression: str) -> ForEachReference: ...
