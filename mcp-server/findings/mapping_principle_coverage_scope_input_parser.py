"""Validates mapping-based principle coverage-scope configuration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from findings.principle_coverage_scope_input import PrincipleCoverageScopeInput
from findings.principle_coverage_scope_input_creating import (
    PrincipleCoverageScopeInputCreating,
)
from findings.principle_coverage_scope_input_parsing import (
    PrincipleCoverageScopeInputParsing,
)


"""
solid-name: MappingPrincipleCoverageScopeInputParser
solid-category: boundary-adapter
solid-description: Validates mapping-based principle applicability configuration into explicit coverage scope inputs.
"""
class MappingPrincipleCoverageScopeInputParser(PrincipleCoverageScopeInputParsing):
    def __init__(self, input_factory: PrincipleCoverageScopeInputCreating) -> None:
        self._input_factory = input_factory

    def parse(
        self,
        raw_scopes: object,
    ) -> tuple[PrincipleCoverageScopeInput, ...]:
        if not isinstance(raw_scopes, Mapping):
            return ()

        inputs: list[PrincipleCoverageScopeInput] = []
        for principle_label, raw_unit_kinds in raw_scopes.items():
            parsed_input = self._parse_input(principle_label, raw_unit_kinds)
            if parsed_input is not None:
                inputs.append(parsed_input)
        return tuple(inputs)

    def _parse_input(
        self,
        principle_label: object,
        raw_unit_kinds: object,
    ) -> PrincipleCoverageScopeInput | None:
        if (
            not isinstance(principle_label, str)
            or not principle_label
            or isinstance(raw_unit_kinds, (str, bytes))
            or not isinstance(raw_unit_kinds, Sequence)
            or not raw_unit_kinds
            or not all(
                isinstance(unit_kind, str) and bool(unit_kind)
                for unit_kind in raw_unit_kinds
            )
        ):
            return None
        return self._input_factory.create(principle_label, raw_unit_kinds)
