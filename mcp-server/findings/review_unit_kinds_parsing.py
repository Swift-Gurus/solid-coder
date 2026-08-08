"""Defines conversion of source-unit kind name sequences."""

from typing import Optional, Protocol

from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: ReviewUnitKindsParsing
solid-category: abstraction
solid-description: Contract for converting validated source-unit kind names into supported domain values.
"""
class ReviewUnitKindsParsing(Protocol):
    def parse(
        self,
        unit_kind_names: tuple[str, ...],
    ) -> Optional[tuple[ReviewUnitKind, ...]]: ...
