"""Rebases included collection metric calculations into local scope."""

from typing import Optional

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.included_metric_calculation_resolving import (
    IncludedMetricCalculationResolving,
)
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.step_output_reference import StepOutputReference


"""
solid-name: IncludedMetricCalculationResolver
solid-category: service
solid-spec: [SPEC-053]
solid-description: Rebases included metric calculations into instance-local scope.
"""
class IncludedMetricCalculationResolver(IncludedMetricCalculationResolving):
    def resolve(
        self,
        calculation: Optional[CollectionMetricCalculation],
        identities: IncludedWorkflowStepIdentities,
    ) -> Optional[CollectionMetricCalculation]:
        if calculation is None:
            return None
        source = calculation.source
        local_identity = identities.require_declaration(source.step_id)
        return CollectionMetricCalculation(
            source=StepOutputReference(
                step_id=local_identity.local_step_id,
                output_name=source.output_name,
            ),
            condition=calculation.condition,
            value=calculation.value,
            source_size=calculation.source_size,
            matched_indexes=calculation.matched_indexes,
            excluded_indexes=calculation.excluded_indexes,
            condition_evidence=calculation.condition_evidence,
        )
