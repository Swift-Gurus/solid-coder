"""Defines restoration of an optional alias-group for-each reference."""

from __future__ import annotations

from typing import Protocol

from harness.step_output_reference import StepOutputReference


"""
solid-name: IncludeAliasGroupForEachParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for restoring an optional for-each reference from one durable alias-group snapshot.
"""
class IncludeAliasGroupForEachParsing(Protocol):
    def parse(
        self,
        alias: str,
        raw: object,
    ) -> StepOutputReference | None: ...
