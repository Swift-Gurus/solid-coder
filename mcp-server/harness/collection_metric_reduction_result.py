"""Defines the deterministic result of one collection metric reducer."""

from dataclasses import dataclass, field
from typing import Union

from harness.collection_metric_projection_evidence import (
    CollectionMetricProjectionEvidence,
)
from harness.condition_evidence import ConditionEvidence


"""
solid-name: CollectionMetricReductionResult
solid-category: model
solid-spec: [SPEC-054]
solid-description: Enables reducer outcomes to be recorded with sufficient evidence for audit and replay.
"""
@dataclass(frozen=True)
class CollectionMetricReductionResult:
    value: Union[int, float]
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
