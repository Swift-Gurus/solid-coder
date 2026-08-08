"""Represents one validated external principle coverage-scope entry."""

from dataclasses import dataclass


"""
solid-name: PrincipleCoverageScopeInput
solid-category: model
solid-description: Carries validated principle coverage scope data between configuration parsing and domain construction.
"""
class PrincipleCoverageScopeInput:
    principle_label: str
    unit_kind_names: tuple[str, ...]


PrincipleCoverageScopeInput = dataclass(frozen=True)(PrincipleCoverageScopeInput)
