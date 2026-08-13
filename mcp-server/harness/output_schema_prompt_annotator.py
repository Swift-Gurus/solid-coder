"""Coordinates output-schema prompt annotation."""

from __future__ import annotations

from harness.output_schema_description_collecting import OutputSchemaDescriptionCollecting
from harness.output_schema_prompt_annotating import OutputSchemaPromptAnnotating
from harness.step_declaration import StepDeclaration
from harness.step_prompt_augmenting import StepPromptAugmenting


"""
solid-name: OutputSchemaPromptAnnotator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Coordinates output-schema description and workflow-step prompt augmentation.
"""
class OutputSchemaPromptAnnotator(OutputSchemaPromptAnnotating):
    def __init__(
        self,
        description_collector: OutputSchemaDescriptionCollecting,
        prompt_augmenter: StepPromptAugmenting,
    ) -> None:
        self._description_collector = description_collector
        self._prompt_augmenter = prompt_augmenter

    def annotate(self, step: StepDeclaration) -> StepDeclaration:
        descriptions = self._description_collector.collect(step.outputs)
        return self._prompt_augmenter.augment(step, descriptions)
