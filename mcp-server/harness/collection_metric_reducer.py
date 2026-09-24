"""Defines one collection metric reducer declaration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.condition_declaration import ConditionDeclaration
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
    value: Optional[WorkflowExpression] = None
    numerator_condition: Optional[ConditionDeclaration] = None
    denominator_condition: Optional[ConditionDeclaration] = None
