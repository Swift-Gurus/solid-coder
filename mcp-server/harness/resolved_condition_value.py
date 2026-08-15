"""Defines the result of resolving a condition reference."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: ResolvedConditionValue
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents the presence and value of a workflow condition reference.
"""
@dataclass(frozen=True)
class ResolvedConditionValue:
    present: bool
    value: object = None
