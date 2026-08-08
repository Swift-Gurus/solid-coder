"""Defines construction of immutable principle coverage-scope collections."""

from typing import Protocol

from findings.principle_coverage_scope import PrincipleCoverageScope
from findings.principle_coverage_scope_input import PrincipleCoverageScopeInput


"""
solid-name: PrincipleCoverageScopesCreating
solid-category: abstraction
solid-description: Contract for constructing immutable principle coverage scopes from validated configuration inputs.
"""
class PrincipleCoverageScopesCreating(Protocol):
    def create(
        self,
        scope_inputs: tuple[PrincipleCoverageScopeInput, ...],
    ) -> tuple[PrincipleCoverageScope, ...]: ...
