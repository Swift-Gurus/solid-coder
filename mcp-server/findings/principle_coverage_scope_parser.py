"""Parses external principle applicability configuration into immutable scopes."""

from findings.principle_coverage_scope import PrincipleCoverageScope
from findings.principle_coverage_scope_input_parsing import (
    PrincipleCoverageScopeInputParsing,
)
from findings.principle_coverage_scope_parsing import PrincipleCoverageScopeParsing
from findings.principle_coverage_scopes_creating import PrincipleCoverageScopesCreating


"""
solid-name: PrincipleCoverageScopeParser
solid-category: boundary-adapter
solid-description: Coordinates validation and construction of immutable principle applicability scopes.
"""
class PrincipleCoverageScopeParser(PrincipleCoverageScopeParsing):
    def __init__(
        self,
        input_parser: PrincipleCoverageScopeInputParsing,
        scopes_factory: PrincipleCoverageScopesCreating,
    ) -> None:
        self._input_parser = input_parser
        self._scopes_factory = scopes_factory

    def parse(self, raw_scopes: object) -> tuple[PrincipleCoverageScope, ...]:
        return self._scopes_factory.create(
            self._input_parser.parse(raw_scopes)
        )
