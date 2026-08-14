"""Defines a parsed workflow for-each output reference."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: ForEachReference
solid-category: model
solid-spec: [SPEC-010, SPEC-030]
solid-description: Identifies the source workflow step and output used for runtime iteration.
"""
@dataclass(frozen=True)
class ForEachReference:
    step_id: str
    output_name: str
