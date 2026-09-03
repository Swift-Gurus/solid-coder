"""Groups ready batch items into ordered authored rule sections."""

from typing import cast

from harness.combined_rule_batch_section import CombinedRuleBatchSection
from harness.combined_rule_batch_sections_building import (
    CombinedRuleBatchSectionsBuilding,
)
from harness.combined_rule_batch_step_presentation import (
    CombinedRuleBatchStepPresentation,
)
from harness.step_result import StepResult


"""
solid-name: CombinedRuleBatchSectionsBuilder
solid-category: service
solid-spec: [SPEC-043]
solid-description: Groups ready batch items into stable authored rule sections for combined rendering.
"""
class CombinedRuleBatchSectionsBuilder(CombinedRuleBatchSectionsBuilding):
    def build(self, steps: list[StepResult]) -> list[CombinedRuleBatchSection]:
        sections: list[CombinedRuleBatchSection] = []
        for step in steps:
            presentation = cast(
                CombinedRuleBatchStepPresentation,
                step.batch,
            )
            matching_index = next(
                (
                    index
                    for index, section in enumerate(sections)
                    if section.rule_alias == presentation.rule_alias
                ),
                None,
            )
            if matching_index is None:
                sections.append(
                    CombinedRuleBatchSection(
                        rule_alias=presentation.rule_alias,
                        prompt=step.prompt,
                        steps=[step],
                    )
                )
                continue
            section = sections[matching_index]
            sections[matching_index] = CombinedRuleBatchSection(
                rule_alias=section.rule_alias,
                prompt=section.prompt,
                steps=[*section.steps, step],
            )
        return sections
