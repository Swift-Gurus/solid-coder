"""Defines deterministic collection input for one metric step."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_source_reference import CollectionSourceReference
from harness.collection_metric_projection_evidence import (
    CollectionMetricProjectionEvidence,
)
from harness.condition_declaration import ConditionDeclaration
from harness.condition_evidence import ConditionEvidence


"""
solid-name: CollectionMetricCalculation
solid-category: model
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Enables deterministic collection-derived metric scoring to be audited and replayed without reevaluation.
"""
@dataclass(frozen=True)
class CollectionMetricCalculation:
    source: CollectionSourceReference
    condition: Optional[ConditionDeclaration] = None
    reducer: Optional[CollectionMetricReducer] = None
    value: Union[int, float] = 0
    source_size: int = 0
    matched_indexes: list[int] = field(default_factory=list)
    excluded_indexes: list[int] = field(default_factory=list)
    condition_evidence: list[ConditionEvidence] = field(default_factory=list)
    projection_evidence: list[CollectionMetricProjectionEvidence] = field(
        default_factory=list
    )
    distinct_indexes: list[int] = field(default_factory=list)
    numerator_indexes: list[int] = field(default_factory=list)
    denominator_indexes: list[int] = field(default_factory=list)
    numerator_condition_evidence: list[ConditionEvidence] = field(
        default_factory=list
    )
    denominator_condition_evidence: list[ConditionEvidence] = field(
        default_factory=list
    )
    zero_denominator: bool = False
