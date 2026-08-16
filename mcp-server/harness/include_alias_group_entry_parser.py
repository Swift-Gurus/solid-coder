"""Restores one include alias group from a durable snapshot entry."""

from collections.abc import Mapping

from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error import FlowValidationError
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_entry_parsing import IncludeAliasGroupEntryParsing
from harness.workflow_input_binding_snapshot_parsing import (
    WorkflowInputBindingSnapshotParsing,
)


"""
solid-name: IncludeAliasGroupEntryParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Restores one validated include group from a workflow snapshot entry.
"""
class IncludeAliasGroupEntryParser(IncludeAliasGroupEntryParsing):

    def __init__(
        self,
        binding_parser: WorkflowInputBindingSnapshotParsing,
        condition_parser: ConditionParsing,
    ) -> None:
        self._binding_parser = binding_parser
        self._condition_parser = condition_parser

    def parse(self, raw: object) -> IncludeAliasGroup:
        if not isinstance(raw, Mapping):
            raise FlowValidationError("Workflow snapshot alias group must be an object")
        alias = raw.get("alias")
        member_ids = raw.get("member_ids")
        depends_on = raw.get("depends_on") or []
        bindings = raw.get("input_bindings") or []
        if not isinstance(alias, str) or not alias:
            raise FlowValidationError("Workflow snapshot alias group requires an alias")
        if not isinstance(member_ids, list) or not all(
            isinstance(member_id, str) for member_id in member_ids
        ):
            raise FlowValidationError(
                f"Workflow snapshot alias group '{alias}' requires member IDs"
            )
        if not isinstance(depends_on, list) or not all(
            isinstance(dependency, str) for dependency in depends_on
        ):
            raise FlowValidationError(
                f"Workflow snapshot alias group '{alias}' has invalid dependencies"
            )
        if not isinstance(bindings, list):
            raise FlowValidationError(
                f"Workflow snapshot alias group '{alias}' has invalid input bindings"
            )
        raw_condition = raw.get("when")
        return IncludeAliasGroup(
            alias=alias,
            member_ids=member_ids,
            depends_on=depends_on,
            for_each=raw.get("for_each") if isinstance(raw.get("for_each"), str) else None,
            input_bindings=[
                self._binding_parser.parse(binding, alias) for binding in bindings
            ],
            condition=(
                self._condition_parser.parse(raw_condition)
                if raw_condition is not None
                else None
            ),
        )
