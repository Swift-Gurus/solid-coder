"""Defines negation of one workflow condition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.condition_declaration import ConditionDeclaration
from harness.condition_runtime import ConditionRuntime


"""
solid-name: NotCondition
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents workflow eligibility that negates one nested criterion.
"""
@dataclass(frozen=True)
class NotCondition(ConditionDeclaration):
    condition: ConditionDeclaration

    def evaluate(
        self,
        runtime: ConditionRuntime,
        context: dict[str, Any],
    ) -> bool:
        return not self.condition.evaluate(runtime, context)
