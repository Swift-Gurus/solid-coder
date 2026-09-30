"""Carries parsed references for a pairwise collection relation."""

from dataclasses import dataclass

from harness.pairwise_relation_operator import PairwiseRelationOperator
from harness.workflow_expression import WorkflowExpression


"""
solid-name: PairwiseRelation
solid-category: model
solid-spec: [SPEC-059]
solid-description: Preserves authored relation references and their parsed item paths for deterministic evaluation.
"""
@dataclass(frozen=True)
class PairwiseRelation:
    operator: PairwiseRelationOperator
    left: WorkflowExpression
    right: WorkflowExpression
    left_path: list[str]
    right_path: list[str]
