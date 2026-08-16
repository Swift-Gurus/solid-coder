"""Parses runtime controls declared on a workflow include."""

from collections.abc import Mapping

from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error import FlowValidationError
from harness.workflow_include_runtime import WorkflowIncludeRuntime
from harness.workflow_include_runtime_parsing import WorkflowIncludeRuntimeParsing
from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: WorkflowIncludeRuntimeParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Validates include-boundary runtime fields and maps them into typed controls.
"""
class WorkflowIncludeRuntimeParser(WorkflowIncludeRuntimeParsing):

    def __init__(self, condition_parser: ConditionParsing) -> None:
        self._condition_parser = condition_parser

    def parse(self, raw: Mapping[str, object]) -> WorkflowIncludeRuntime:
        depends_on = raw.get("depends_on") or []
        if not isinstance(depends_on, list) or not all(
            isinstance(dependency, str) and dependency
            for dependency in depends_on
        ):
            raise FlowValidationError(
                "Workflow include 'depends_on' must be an array of non-empty strings"
            )

        for_each = raw.get("for_each")
        if for_each is not None and (
            not isinstance(for_each, str) or not for_each
        ):
            raise FlowValidationError(
                "Workflow include 'for_each' must be a non-empty string"
            )

        raw_bindings = raw.get("with") or {}
        if not isinstance(raw_bindings, Mapping) or not all(
            isinstance(name, str)
            and name
            and isinstance(expression, str)
            and expression
            for name, expression in raw_bindings.items()
        ):
            raise FlowValidationError(
                "Workflow include 'with' must map input names to non-empty expressions"
            )

        raw_condition = raw.get("when")
        condition = (
            self._condition_parser.parse(raw_condition)
            if raw_condition is not None
            else None
        )
        return WorkflowIncludeRuntime(
            depends_on=list(depends_on),
            for_each=for_each,
            input_bindings=[
                WorkflowInputBinding(name=name, expression=expression)
                for name, expression in raw_bindings.items()
            ],
            condition=condition,
        )
