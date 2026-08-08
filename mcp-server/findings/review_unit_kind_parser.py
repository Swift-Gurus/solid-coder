"""Converts external source-unit kind values into the closed domain enum."""

from typing import Optional

from findings.review_unit_kind import ReviewUnitKind
from findings.review_unit_kind_parsing import ReviewUnitKindParsing


"""
solid-name: ReviewUnitKindParser
solid-category: boundary-adapter
solid-description: Converts one external string value into a supported source-unit kind.
"""
class ReviewUnitKindParser(ReviewUnitKindParsing):
    def parse(self, raw_unit_kind: object) -> Optional[ReviewUnitKind]:
        if not isinstance(raw_unit_kind, str):
            return None
        try:
            return ReviewUnitKind(raw_unit_kind)
        except ValueError:
            return None
