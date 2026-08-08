"""Constructs validated principle coverage-scope input values."""

from collections.abc import Iterable

from findings.principle_coverage_scope_input import PrincipleCoverageScopeInput
from findings.principle_coverage_scope_input_creating import (
    PrincipleCoverageScopeInputCreating,
)


"""
solid-name: PrincipleCoverageScopeInputFactory
solid-category: factory
solid-description: Constructs validated principle coverage scope inputs from external configuration values.
"""
class PrincipleCoverageScopeInputFactory(PrincipleCoverageScopeInputCreating):
    def create(
        self,
        principle_label: str,
        unit_kind_names: Iterable[str],
    ) -> PrincipleCoverageScopeInput:
        return PrincipleCoverageScopeInput(
            principle_label=principle_label,
            unit_kind_names=tuple(unit_kind_names),
        )
