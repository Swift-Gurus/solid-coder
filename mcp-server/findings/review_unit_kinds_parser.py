"""Converts source-unit kind name sequences into supported domain values."""

from typing import Optional

from findings.review_unit_kind import ReviewUnitKind
from findings.review_unit_kind_parsing import ReviewUnitKindParsing
from findings.review_unit_kinds_parsing import ReviewUnitKindsParsing


"""
solid-name: ReviewUnitKindsParser
solid-category: boundary-adapter
solid-description: Converts a validated source-unit kind sequence and rejects unsupported values as one unit.
"""
class ReviewUnitKindsParser(ReviewUnitKindsParsing):
    def __init__(self, unit_kind_parser: ReviewUnitKindParsing) -> None:
        self._unit_kind_parser = unit_kind_parser

    def parse(
        self,
        unit_kind_names: tuple[str, ...],
    ) -> Optional[tuple[ReviewUnitKind, ...]]:
        unit_kinds = tuple(
            self._unit_kind_parser.parse(unit_kind_name)
            for unit_kind_name in unit_kind_names
        )
        if not unit_kinds or any(unit_kind is None for unit_kind in unit_kinds):
            return None
        return tuple(unit_kind for unit_kind in unit_kinds if unit_kind is not None)
