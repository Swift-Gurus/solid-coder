"""Assembles batch output mapping for every presentation mode."""

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
                ]
            )
        )
