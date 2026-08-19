"""Combines optional workflow conditions into one typed conjunction."""

from __future__ import annotations

from harness.all_condition import AllCondition
from harness.condition_conjoining import ConditionConjoining
from harness.condition_declaration import ConditionDeclaration


"""
solid-name: ConditionConjoiner
solid-category: service
solid-spec: [SPEC-037, SPEC-039]
solid-description: Preserves zero or one condition and joins multiple conditions with logical all.
"""
class ConditionConjoiner(ConditionConjoining):
    def conjoin(
        self,
        conditions: list[ConditionDeclaration | None],
    ) -> ConditionDeclaration | None:
        present = [condition for condition in conditions if condition is not None]
        if not present:
            return None
        if len(present) == 1:
            return present[0]
        return AllCondition(conditions=tuple(present))
