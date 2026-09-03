"""Defines one rule section inside a combined batched model presentation."""

from dataclasses import dataclass

from harness.batch_step_presentation import BatchStepPresentation
from harness.batch_step_presentation_mode import BatchStepPresentationMode


"""
solid-name: CombinedRuleBatchStepPresentation
solid-category: model
solid-spec: [SPEC-043]
solid-description: Adds the authored rule alias to an ordinary domain-labeled batch item participating in a combined group.
"""
@dataclass(frozen=True)
class CombinedRuleBatchStepPresentation(BatchStepPresentation):
    rule_alias: str

    @property
    def mode(self) -> BatchStepPresentationMode:
        return BatchStepPresentationMode.COMBINED_RULES
