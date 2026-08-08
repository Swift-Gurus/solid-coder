"""Defines validation of external principle coverage-scope entries."""

from typing import Protocol

from findings.principle_coverage_scope_input import PrincipleCoverageScopeInput


"""
solid-name: PrincipleCoverageScopeInputParsing
solid-category: abstraction
solid-description: Contract for validating external principle coverage scope configuration into explicit input models.
"""
class PrincipleCoverageScopeInputParsing(Protocol):
    def parse(
        self,
        raw_scopes: object,
    ) -> tuple[PrincipleCoverageScopeInput, ...]: ...
