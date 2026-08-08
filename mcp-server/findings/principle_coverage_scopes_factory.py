"""Constructs immutable principle coverage-scope collections."""

from __future__ import annotations

from findings.principle_coverage_scope import PrincipleCoverageScope
from findings.principle_coverage_scope_creating import PrincipleCoverageScopeCreating
from findings.principle_coverage_scope_input import PrincipleCoverageScopeInput
from findings.principle_coverage_scopes_creating import PrincipleCoverageScopesCreating
from findings.review_unit_kinds_parsing import ReviewUnitKindsParsing


"""
solid-name: PrincipleCoverageScopesFactory
solid-category: factory
solid-description: Constructs supported principle coverage scopes from validated configuration inputs.
"""
class PrincipleCoverageScopesFactory(PrincipleCoverageScopesCreating):
    def __init__(
        self,
        unit_kinds_parser: ReviewUnitKindsParsing,
        scope_factory: PrincipleCoverageScopeCreating,
    ) -> None:
        self._unit_kinds_parser = unit_kinds_parser
        self._scope_factory = scope_factory

    def create(
        self,
        scope_inputs: tuple[PrincipleCoverageScopeInput, ...],
    ) -> tuple[PrincipleCoverageScope, ...]:
        scopes: list[PrincipleCoverageScope] = []
        for scope_input in scope_inputs:
            scope = self._create_scope(scope_input)
            if scope is not None:
                scopes.append(scope)
        return tuple(scopes)

    def _create_scope(
        self,
        scope_input: PrincipleCoverageScopeInput,
    ) -> PrincipleCoverageScope | None:
        unit_kinds = self._unit_kinds_parser.parse(scope_input.unit_kind_names)
        if unit_kinds is None:
            return None
        return self._scope_factory.create(scope_input.principle_label, unit_kinds)
