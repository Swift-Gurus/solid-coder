"""Defines construction of validated principle coverage-scope inputs."""

from collections.abc import Iterable
from typing import Protocol

from findings.principle_coverage_scope_input import PrincipleCoverageScopeInput


"""
solid-name: PrincipleCoverageScopeInputCreating
solid-category: abstraction
solid-description: Contract for constructing validated principle coverage scope input values.
"""
class PrincipleCoverageScopeInputCreating(Protocol):
    def create(
        self,
        principle_label: str,
        unit_kind_names: Iterable[str],
    ) -> PrincipleCoverageScopeInput: ...
