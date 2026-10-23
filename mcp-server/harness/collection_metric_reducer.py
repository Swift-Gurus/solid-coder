"""Defines one collection metric reducer declaration."""

from __future__ import annotations

from dataclasses import dataclass

from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.condition_declaration import ConditionDeclaration
from harness.pairwise_relation import PairwiseRelation
from harness.workflow_expression import WorkflowExpression

"""
solid-name: CollectionMetricReducer
solid-category: model
solid-spec: [SPEC-054]
solid-description: Represents one validated deterministic collection reducer.
"""


@dataclass(frozen=True)
class CollectionMetricReducer:
    type: CollectionMetricReducerType
    value: WorkflowExpression | None = None
    empty_value: int | float | None = None
    numerator_condition: ConditionDeclaration | None = None
    denominator_condition: ConditionDeclaration | None = None
    relation: PairwiseRelation | None = None
