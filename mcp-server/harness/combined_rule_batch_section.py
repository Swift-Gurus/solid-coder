"""Defines one authored rule section in a combined batch presentation."""

from dataclasses import dataclass

from harness.step_result import StepResult


"""
solid-name: CombinedRuleBatchSection
solid-category: model
solid-spec: [SPEC-043]
solid-description: Carries one authored rule prompt and its applicable ready batch items for combined rendering.
"""
@dataclass(frozen=True)
class CombinedRuleBatchSection:
    rule_alias: str
    prompt: str
    steps: list[StepResult]
