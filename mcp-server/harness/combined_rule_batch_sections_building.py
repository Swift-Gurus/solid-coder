"""Defines construction of combined rule-presentation sections."""

from typing import Protocol

from harness.combined_rule_batch_section import CombinedRuleBatchSection
from harness.step_result import StepResult


"""
solid-name: CombinedRuleBatchSectionsBuilding
solid-category: abstraction
solid-spec: [SPEC-043]
solid-description: Contract for grouping ready batch items into authored rule sections.
"""
class CombinedRuleBatchSectionsBuilding(Protocol):
    def build(self, steps: list[StepResult]) -> list[CombinedRuleBatchSection]: ...
