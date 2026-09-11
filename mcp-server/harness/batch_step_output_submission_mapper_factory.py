"""Assembles batch output mapping for every presentation mode."""

from harness.aggregate_batch_output_submission_mapper import (
    AggregateBatchOutputSubmissionMapper,
)
from harness.batch_submission_target_resolver import BatchSubmissionTargetResolver
from harness.batch_presentation_capability_registration import (
    BatchPresentationCapabilityRegistration,
)
from harness.batch_presentation_capability_resolver import (
    BatchPresentationCapabilityResolver,
)
from harness.batch_step_output_submission_mapper import (
    BatchStepOutputSubmissionMapper,
)
from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.combined_rule_batch_output_submission_mapper import (
    CombinedRuleBatchOutputSubmissionMapper,
)
from harness.ordinary_batch_output_submission_mapper import (
    OrdinaryBatchOutputSubmissionMapper,
)
from harness.rejected_step_output_mapping_builder import RejectedStepOutputMappingBuilder
from harness.successful_step_output_mapping_builder import SuccessfulStepOutputMappingBuilder


"""
solid-name: BatchStepOutputSubmissionMapperFactory
solid-category: factory
solid-spec: [SPEC-042, SPEC-043]
solid-description: Assembles batch output-submission mapping for every supported presentation mode.
"""
class BatchStepOutputSubmissionMapperFactory:
    def make(self) -> BatchStepOutputSubmissionMapper:
        return BatchStepOutputSubmissionMapper(
            mappers=BatchPresentationCapabilityResolver(
                registrations=[
                    BatchPresentationCapabilityRegistration(
                        mode=BatchStepPresentationMode.ORDINARY,
                        capability=OrdinaryBatchOutputSubmissionMapper(),
                    ),
                    BatchPresentationCapabilityRegistration(
                        mode=BatchStepPresentationMode.COMBINED_RULES,
                        capability=CombinedRuleBatchOutputSubmissionMapper(),
                    ),
                    BatchPresentationCapabilityRegistration(
                        mode=BatchStepPresentationMode.AGGREGATE,
                        capability=AggregateBatchOutputSubmissionMapper(
                            target_resolver=BatchSubmissionTargetResolver(),
                            success_builder=SuccessfulStepOutputMappingBuilder(),
                            rejection_builder=RejectedStepOutputMappingBuilder(),
                        ),
                    ),
                ]
            )
        )
