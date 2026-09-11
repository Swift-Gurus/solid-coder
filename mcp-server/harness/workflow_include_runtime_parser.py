"""Parses runtime controls declared on a workflow include."""

from __future__ import annotations

from collections.abc import Mapping

from harness.condition_parsing import ConditionParsing
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.for_each_declaration_parsing import ForEachDeclarationParsing
from harness.structured_mode_resolver import StructuredModeResolver
from harness.workflow_execution_declaration import WorkflowExecutionDeclaration
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_include_runtime import WorkflowIncludeRuntime
from harness.workflow_include_runtime_parsing import WorkflowIncludeRuntimeParsing
from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_expression_parsing import WorkflowExpressionParsing
from harness.workflow_presentation_declaration import WorkflowPresentationDeclaration
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: WorkflowIncludeRuntimeParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Validates include-boundary runtime fields and maps them into typed controls.
"""
class WorkflowIncludeRuntimeParser(WorkflowIncludeRuntimeParsing):

    def __init__(
        self,
        condition_parser: ConditionParsing,
        for_each_parser: ForEachDeclarationParsing,
        expression_parser: WorkflowExpressionParsing,
        execution_resolver: StructuredModeResolver[
            WorkflowExecutionDeclaration,
            WorkflowExecutionMode,
        ],
        presentation_resolver: StructuredModeResolver[
            WorkflowPresentationDeclaration,
            WorkflowPresentationMode,
        ],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._condition_parser = condition_parser
        self._for_each_parser = for_each_parser
        self._expression_parser = expression_parser
        self._execution_resolver = execution_resolver
        self._presentation_resolver = presentation_resolver
        self._error_factory = error_factory

    def parse(
        self,
        raw: Mapping[str, object],
        policy_source: Mapping[str, object] | None = None,
    ) -> WorkflowIncludeRuntime:
        depends_on = raw.get("depends_on") or []
        if not isinstance(depends_on, list) or not all(
            isinstance(dependency, str) and dependency
            for dependency in depends_on
        ):
            raise self._error_factory.create(
                "Workflow include 'depends_on' must be an array of non-empty strings"
            )

        for_each = raw.get("for_each")
        if for_each is not None and (
            not isinstance(for_each, (str, Mapping)) or not for_each
        ):
            raise self._error_factory.create(
                "Workflow include 'for_each' must be a non-empty expression or reference"
            )

        raw_bindings = raw.get("with") or {}
        if not isinstance(raw_bindings, Mapping) or not all(
            isinstance(name, str)
            and name
            and isinstance(expression, str)
            and expression
            for name, expression in raw_bindings.items()
        ):
            raise self._error_factory.create(
                "Workflow include 'with' must map input names to non-empty expressions"
            )

        raw_condition = raw.get("when")
        condition = (
            self._condition_parser.parse(raw_condition)
            if raw_condition is not None
            else None
        )
        defaults = WorkflowIncludeRuntime()
        if policy_source is not None:
            defaults = WorkflowIncludeRuntime(
                execution=self._execution_resolver.resolve(
                    policy_source,
                    defaults.execution,
                ),
                presentation=self._presentation_resolver.resolve(
                    policy_source,
                    defaults.presentation,
                ),
            )
        return WorkflowIncludeRuntime(
            depends_on=list(depends_on),
            for_each=(
                self._for_each_parser.parse("workflow include", for_each)
                if isinstance(for_each, (str, Mapping))
                else None
            ),
            input_bindings=[
                WorkflowInputBinding(
                    name=name,
                    expression=self._expression_parser.parse(expression),
                )
                for name, expression in raw_bindings.items()
            ],
            condition=condition,
            execution=self._execution_resolver.resolve(raw, defaults.execution),
            presentation=self._presentation_resolver.resolve(
                raw,
                defaults.presentation,
            ),
        )
