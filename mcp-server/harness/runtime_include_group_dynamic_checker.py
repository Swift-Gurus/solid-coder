"""Identifies include groups that require runtime materialization."""

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_dynamic_checking import IncludeGroupDynamicChecking


"""
solid-name: RuntimeIncludeGroupDynamicChecker
solid-category: service
solid-spec: [SPEC-037, SPEC-045]
solid-description: Identifies executable include groups requiring runtime instance materialization.
"""
class RuntimeIncludeGroupDynamicChecker(IncludeGroupDynamicChecking):
    def is_dynamic(self, group: IncludeAliasGroup) -> bool:
        has_runtime_controls = bool(
            group.depends_on
            or group.for_each is not None
            or group.input_bindings
            or group.condition is not None
            or group.rule_workflow is not None
            or group.outputs
        )
        return has_runtime_controls or bool(group.member_ids)
