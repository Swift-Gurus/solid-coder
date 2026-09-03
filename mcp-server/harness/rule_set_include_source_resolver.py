"""Resolves the explicit all-rules workflow include source."""

from __future__ import annotations

from harness.include_source import IncludeSource
from harness.rule_set_include_reference_parsing import (
    RuleSetIncludeReferenceParsing,
)
from harness.rule_set_member_serializing import RuleSetMemberSerializing
from harness.rule_set_members_resolving import RuleSetMembersResolving
from harness.workflow_include_runtime import WorkflowIncludeRuntime
from harness.workflow_include_runtime_parsing import WorkflowIncludeRuntimeParsing


"""
solid-name: RuleSetIncludeSourceResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Expands an explicit all-rules include from the scoped catalog in stable workflow-ID order.
"""
class RuleSetIncludeSourceResolver:
    def __init__(
        self,
        reference_parser: RuleSetIncludeReferenceParsing,
        runtime_parser: WorkflowIncludeRuntimeParsing,
        members_resolver: RuleSetMembersResolving,
        member_serializer: RuleSetMemberSerializing,
    ) -> None:
        self._reference_parser = reference_parser
        self._runtime_parser = runtime_parser
        self._members_resolver = members_resolver
        self._member_serializer = member_serializer

    def resolve(
        self,
        entry: dict,
        flow_file_path: str,
        search_paths: list[str],
    ) -> IncludeSource | None:
        declaration = self._reference_parser.parse(entry.get("include"))
        if declaration is None:
            return None

        runtime = self._runtime_parser.parse(entry)
        members = self._members_resolver.resolve(search_paths, runtime)
        return IncludeSource(
            alias=entry["as"],
            steps=[
                self._member_serializer.serialize(member)
                for member in members
            ],
            flow_path=flow_file_path,
            runtime=WorkflowIncludeRuntime(
                presentation=runtime.presentation,
            ),
            identity="rules:all",
            label="rules:all",
        )
