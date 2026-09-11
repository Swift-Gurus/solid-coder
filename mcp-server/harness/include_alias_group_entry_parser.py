"""Restores one include alias group from a durable snapshot entry."""

from __future__ import annotations

from collections.abc import Mapping

from harness.condition_parsing import ConditionParsing
from harness.combined_rule_presentation import CombinedRulePresentation
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_entry_parsing import IncludeAliasGroupEntryParsing
from harness.include_alias_group_for_each_parsing import (
    IncludeAliasGroupForEachParsing,
)
from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.structured_model_decoding import StructuredModelDecoding
from harness.structured_mode_resolver import StructuredModeResolver
from harness.workflow_execution_declaration import WorkflowExecutionDeclaration
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_input_binding_snapshot_parsing import (
    WorkflowInputBindingSnapshotParsing,
)
from harness.workflow_output_declaration_parser import WorkflowOutputDeclarationParser
from harness.workflow_presentation_declaration import WorkflowPresentationDeclaration
from harness.workflow_presentation_mode import WorkflowPresentationMode


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
        for_each_parser: IncludeAliasGroupForEachParsing,
        rule_workflow_decoder: StructuredModelDecoding[IncludedRuleWorkflow],
        combined_presentation_decoder: StructuredModelDecoding[CombinedRulePresentation],
        execution_resolver: StructuredModeResolver[
            WorkflowExecutionDeclaration,
            WorkflowExecutionMode,
        ],
        presentation_resolver: StructuredModeResolver[
            WorkflowPresentationDeclaration,
            WorkflowPresentationMode,
        ],
        output_parser: WorkflowOutputDeclarationParser,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._binding_parser = binding_parser
        self._condition_parser = condition_parser
        self._for_each_parser = for_each_parser
        self._rule_workflow_decoder = rule_workflow_decoder
        self._combined_presentation_decoder = combined_presentation_decoder
        self._execution_resolver = execution_resolver
        self._presentation_resolver = presentation_resolver
        self._output_parser = output_parser
        self._error_factory = error_factory

    def parse(self, raw: object) -> IncludeAliasGroup:
        if not isinstance(raw, Mapping):
            raise self._error_factory.create(
                "Workflow snapshot alias group must be an object"
            )
        alias = raw.get("alias")
        authored_alias = raw.get("authored_alias")
        owner_alias = raw.get("owner_alias")
        runtime_owner_instance_id = raw.get("runtime_owner_instance_id")
        member_ids = raw.get("member_ids")
        depends_on = raw.get("depends_on") or []
        bindings = raw.get("input_bindings") or []
        if not isinstance(alias, str) or not alias:
            raise self._error_factory.create(
                "Workflow snapshot alias group requires an alias"
            )
        if not isinstance(authored_alias, str) or not authored_alias:
            raise self._error_factory.create(
                f"Workflow snapshot alias group '{alias}' requires an authored alias"
            )
        if owner_alias is not None and (
            not isinstance(owner_alias, str) or not owner_alias
        ):
            raise self._error_factory.create(
                f"Workflow snapshot alias group '{alias}' has an invalid owner alias"
            )
        if runtime_owner_instance_id is not None and (
            not isinstance(runtime_owner_instance_id, str)
            or not runtime_owner_instance_id
        ):
            raise self._error_factory.create(
                f"Workflow snapshot alias group '{alias}' has an invalid runtime owner"
            )
        if not isinstance(member_ids, list) or not all(
            isinstance(member_id, str) for member_id in member_ids
        ):
            raise self._error_factory.create(
                f"Workflow snapshot alias group '{alias}' requires member IDs"
            )
        if not isinstance(depends_on, list) or not all(
            isinstance(dependency, str) for dependency in depends_on
        ):
            raise self._error_factory.create(
                f"Workflow snapshot alias group '{alias}' has invalid dependencies"
            )
        if not isinstance(bindings, list):
            raise self._error_factory.create(
                f"Workflow snapshot alias group '{alias}' has invalid input bindings"
            )
        raw_condition = raw.get("when")
        raw_for_each = raw.get("for_each")
        return IncludeAliasGroup(
            alias=alias,
            member_ids=member_ids,
            authored_alias=authored_alias,
            owner_alias=owner_alias,
            runtime_owner_instance_id=runtime_owner_instance_id,
            depends_on=depends_on,
            for_each=self._for_each_parser.parse(alias, raw_for_each),
            input_bindings=[
                self._binding_parser.parse(binding, alias) for binding in bindings
            ],
            condition=(
                self._condition_parser.parse(raw_condition)
                if raw_condition is not None
                else None
            ),
            rule_workflow=(
                self._rule_workflow_decoder.decode(
                    raw["rule_workflow"],
                    f"workflow snapshot alias group '{alias}' rule ownership",
                )
                if raw.get("rule_workflow") is not None
                else None
            ),
            outputs=self._output_parser.parse(
                raw.get("outputs"),
                "<workflow-snapshot>",
            ),
            execution=self._execution_resolver.resolve(
                raw,
                WorkflowExecutionMode.GRANULAR,
            ),
            presentation=self._presentation_resolver.resolve(
                raw,
                WorkflowPresentationMode.INDIVIDUAL,
            ),
            combined_presentation=(
                self._combined_presentation_decoder.decode(
                    raw["combined_presentation"],
                    f"workflow snapshot alias group '{alias}' combined presentation",
                )
                if raw.get("combined_presentation") is not None
                else None
            ),
        )
