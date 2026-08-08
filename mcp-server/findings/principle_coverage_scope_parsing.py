"""Defines parsing of principle unit-coverage scope configuration."""

from typing import Protocol

from findings.principle_coverage_scope import PrincipleCoverageScope


"""
solid-name: PrincipleCoverageScopeParsing
solid-category: abstraction
solid-description: Contract for converting external principle applicability configuration into immutable coverage scopes.
"""
class PrincipleCoverageScopeParsing(Protocol):
    def parse(self, raw_scopes: object) -> tuple[PrincipleCoverageScope, ...]: ...
