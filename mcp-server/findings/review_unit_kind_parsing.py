"""Defines conversion of external source-unit kind values."""

from typing import Optional, Protocol

from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: ReviewUnitKindParsing
solid-category: abstraction
solid-description: Contract for converting one external value into a supported source-unit kind.
"""
class ReviewUnitKindParsing(Protocol):
    def parse(self, raw_unit_kind: object) -> Optional[ReviewUnitKind]: ...
