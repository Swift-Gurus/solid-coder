"""Rewrites typed conditions into durable workflow snapshot fields."""

from __future__ import annotations

from harness.condition_declaration import ConditionDeclaration
from harness.condition_field_rewriting import ConditionFieldRewriting
from harness.condition_serializing import ConditionSerializing


"""
solid-name: ConditionFieldRewriter
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Maintains durable workflow condition state by translating declared conditions into snapshot-ready representations.
"""
class ConditionFieldRewriter(ConditionFieldRewriting):

    def __init__(self, condition_serializer: ConditionSerializing) -> None:
        self._condition_serializer = condition_serializer

    def rewrite(
        self,
        target: dict[str, object],
        condition: ConditionDeclaration | None,
    ) -> None:
        target.pop("condition", None)
        if condition is not None:
            target["when"] = self._condition_serializer.serialize(condition)
