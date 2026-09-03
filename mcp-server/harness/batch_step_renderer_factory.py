"""Assembles batch rendering for every presentation mode."""

from harness.batch_step_item_renderer import BatchStepItemRenderer
from harness.batch_presentation_capability_registration import (
    BatchPresentationCapabilityRegistration,
)
from harness.batch_presentation_capability_resolver import (
    BatchPresentationCapabilityResolver,
)
from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.batch_step_renderer import BatchStepRenderer
from harness.combined_rule_batch_sections_builder import (
    CombinedRuleBatchSectionsBuilder,
)
from harness.combined_rule_batch_step_renderer import (
    CombinedRuleBatchStepRenderer,
)
from harness.ordinary_batch_step_renderer import OrdinaryBatchStepRenderer


"""
solid-name: BatchStepRendererFactory
solid-category: factory
solid-spec: [SPEC-042, SPEC-043]
solid-description: Assembles model-facing batch rendering for every supported presentation mode.
"""
class BatchStepRendererFactory:
    def make(self) -> BatchStepRenderer:
        item_renderer = BatchStepItemRenderer()
        return BatchStepRenderer(
            renderers=BatchPresentationCapabilityResolver(
                registrations=[
                    BatchPresentationCapabilityRegistration(
                        mode=BatchStepPresentationMode.ORDINARY,
                        capability=OrdinaryBatchStepRenderer(item_renderer),
                    ),
                    BatchPresentationCapabilityRegistration(
                        mode=BatchStepPresentationMode.COMBINED_RULES,
                        capability=CombinedRuleBatchStepRenderer(
                            sections=CombinedRuleBatchSectionsBuilder(),
                            item_renderer=item_renderer,
                        ),
                    ),
                ]
            )
        )
