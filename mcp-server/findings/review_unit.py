"""Defines one immutable source-code unit in a review submission."""

from __future__ import annotations

from dataclasses import field
from typing import Annotated, Optional

from pydantic import AliasChoices, ConfigDict, Field
from pydantic.dataclasses import dataclass

from findings.principle_metrics import PrincipleMetrics
from findings.review_unit_kind import ReviewUnitKind
from findings.review_violation import ReviewViolation


"""
solid-name: ReviewUnit
solid-category: model
solid-description: Represents one reviewed source-code unit and its principle measurements.
"""
@dataclass(frozen=True, config=ConfigDict(extra="forbid", populate_by_name=True))
class ReviewUnit:
    name: Annotated[str, Field(validation_alias=AliasChoices("name", "unit_name"))]
    kind: Annotated[ReviewUnitKind, Field(validation_alias=AliasChoices("kind", "unit_kind"))]
    metrics: tuple[PrincipleMetrics, ...]
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    violations: tuple[ReviewViolation, ...] = field(default_factory=tuple)
