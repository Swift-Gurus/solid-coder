"""Renders several applicable rule sections in one model-facing batch."""

from harness.batch_step_item_rendering import BatchStepItemRendering
from harness.batch_step_rendering import BatchStepRendering
from harness.combined_rule_batch_sections_building import (
    CombinedRuleBatchSectionsBuilding,
)
from harness.step_result import StepResult


"""
solid-name: CombinedRuleBatchStepRenderer
solid-category: service
solid-spec: [SPEC-043]
solid-description: Renders applicable authored rule sections and domain-labelled items in one model-facing batch.
"""
class CombinedRuleBatchStepRenderer(BatchStepRendering):
    def __init__(
        self,
        sections: CombinedRuleBatchSectionsBuilding,
        item_renderer: BatchStepItemRendering,
    ) -> None:
        self._sections = sections
        self._item_renderer = item_renderer

    def render(self, steps: list[StepResult]) -> str:
        sections = self._sections.build(steps)
        rendered_sections = "\n\n".join(
            (
                f"Rule: {section.rule_alias}\n"
                "Applicable items:\n"
                + "\n".join(
                    self._item_renderer.render(step)
                    for step in section.steps
                )
                + "\n\n"
                + section.prompt
            )
            for section in sections
        )
        return (
            "Apply every rule section below to every item listed in that section.\n\n"
            f"{rendered_sections}\n\n"
            "Call flow_next with outputs as one object keyed first by the exact "
            "item label and then by the exact rule alias. Each rule value must "
            "match that rule section's declared outputs.\n"
            "Shape: {\"<item label>\": {\"<rule alias>\": "
            "{\"<declared output>\": \"<value>\"}}}"
        )
