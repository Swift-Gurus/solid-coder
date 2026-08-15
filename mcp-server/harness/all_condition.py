"""Defines conjunction of workflow conditions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.condition_declaration import ConditionDeclaration
from harness.condition_runtime import ConditionRuntime


"""
solid-name: AllCondition
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents workflow eligibility that requires every nested criterion.
"""
@dataclass(frozen=True)
class AllCondition(ConditionDeclaration):
    conditions: tuple[ConditionDeclaration, ...]

    def evaluate(
        self,
        runtime: ConditionRuntime,
        context: dict[str, Any],
    ) -> bool:
        return all(condition.evaluate(runtime, context) for condition in self.conditions)
