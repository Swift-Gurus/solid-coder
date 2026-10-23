"""Rebases included collection metric calculations into local scope."""

from dataclasses import replace

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.included_metric_calculation_resolving import (
    IncludedMetricCalculationResolving,
)
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.step_output_reference import StepOutputReference

"""
solid-name: IncludedMetricCalculationResolver
solid-category: adapter
solid-spec: [SPEC-053, SPEC-054, SPEC-056]
solid-description: Preserves deterministic metric behavior while adapting source identities into an included workflow scope.
"""


class IncludedMetricCalculationResolver(IncludedMetricCalculationResolving):
    def resolve(
        self,
        calculation: CollectionMetricCalculation | None,
        identities: IncludedWorkflowStepIdentities,
    ) -> CollectionMetricCalculation | None:
        if calculation is None:
            return None
        source = calculation.source
        if not isinstance(source, StepOutputReference):
            return calculation
        local_identity = next(
            entry
            for entry in identities.entries
            if entry.declaration_id == source.step_id
        )
        return replace(
            calculation,
            source=replace(
                source,
                step_id=local_identity.local_step_id,
            ),
        )
