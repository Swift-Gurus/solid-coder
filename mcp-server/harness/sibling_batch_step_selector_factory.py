"""Assembles batch sibling selection for every presentation mode."""

from harness.batch_presentation_capability_registration import (
    BatchPresentationCapabilityRegistration,
)
from harness.batch_presentation_capability_resolver import (
    BatchPresentationCapabilityResolver,
)
from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.combined_rule_batch_step_group_validator import (
    CombinedRuleBatchStepGroupValidator,
)
from harness.ordinary_batch_step_group_validator import (
    OrdinaryBatchStepGroupValidator,
)
from harness.sibling_batch_step_selector import SiblingBatchStepSelector


"""
solid-name: SiblingBatchStepSelectorFactory
solid-category: factory
solid-spec: [SPEC-042, SPEC-043]
solid-description: Assembles sibling batch selection with validators for every supported presentation mode.
"""
class SiblingBatchStepSelectorFactory:
    def make(self) -> SiblingBatchStepSelector:
        return SiblingBatchStepSelector(
            validators=BatchPresentationCapabilityResolver(
                registrations=[
                    BatchPresentationCapabilityRegistration(
                        mode=BatchStepPresentationMode.ORDINARY,
                        capability=OrdinaryBatchStepGroupValidator(),
                    ),
                    BatchPresentationCapabilityRegistration(
                        mode=BatchStepPresentationMode.COMBINED_RULES,
                        capability=CombinedRuleBatchStepGroupValidator(),
                    ),
                ]
            )
        )
