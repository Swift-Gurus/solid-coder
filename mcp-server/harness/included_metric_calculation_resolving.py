"""Defines runtime rebasing of included collection metric calculations."""

from typing import Protocol

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities

"""
solid-name: IncludedMetricCalculationResolving
solid-category: abstraction
solid-spec: [SPEC-053]
solid-description: Contract for rebasing included metric calculations into instance-local scope.
"""


class IncludedMetricCalculationResolving(Protocol):
    def resolve(
        self,
        calculation: CollectionMetricCalculation | None,
        identities: IncludedWorkflowStepIdentities,
    ) -> CollectionMetricCalculation | None: ...
