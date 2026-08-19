"""Adapts typed rule-set members to raw workflow include entries."""

from harness.condition_serializing import ConditionSerializing
from harness.rule_set_member_include import RuleSetMemberInclude
from harness.rule_set_member_serializing import RuleSetMemberSerializing


"""
solid-name: RuleSetMemberSerializer
solid-category: boundary
solid-spec: [SPEC-039]
solid-description: Translates typed rule-set members into workflow inclusion data.
"""
class RuleSetMemberSerializer(RuleSetMemberSerializing):
    def __init__(self, condition_serializer: ConditionSerializing) -> None:
        self._condition_serializer = condition_serializer

    def serialize(self, member: RuleSetMemberInclude) -> dict[str, object]:
        runtime = member.runtime
        result: dict[str, object] = {
            "include": {"workflow": member.workflow_id},
            "as": member.alias,
        }
        if runtime.depends_on:
            result["depends_on"] = list(runtime.depends_on)
        if runtime.for_each is not None:
            result["for_each"] = {
                "step_id": runtime.for_each.step_id,
                "output_name": runtime.for_each.output_name,
            }
        if runtime.input_bindings:
            result["with"] = {
                binding.name: f"{{{{{binding.expression.value}}}}}"
                for binding in runtime.input_bindings
            }
        if member.condition is not None:
            result["when"] = self._condition_serializer.serialize(
                member.condition
            )
        return result
