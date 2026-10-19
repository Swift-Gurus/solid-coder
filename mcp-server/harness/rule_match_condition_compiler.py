"""Compiles typed rule applicability into reusable workflow conditions."""

from __future__ import annotations

from harness.condition_conjoining import ConditionConjoining
from harness.condition_declaration import ConditionDeclaration
from harness.condition_operator import ConditionOperator
from harness.flow_validation_error import FlowValidationError
from harness.rule_match_condition_compiling import RuleMatchConditionCompiling
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_selection_condition_compiling import (
    RuleSelectionConditionCompiling,
)
from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: RuleMatchConditionCompiler
solid-category: service
solid-spec: [SPEC-039]
solid-description: Compiles exact extension, unit-kind, and tag selectors into auditable workflow conditions.
"""
class RuleMatchConditionCompiler(RuleMatchConditionCompiling):
    def __init__(
        self,
        selection_compiler: RuleSelectionConditionCompiling,
        condition_conjoiner: ConditionConjoining,
    ) -> None:
        self._selection_compiler = selection_compiler
        self._condition_conjoiner = condition_conjoiner

    def compile(
        self,
        declaration: RuleMatchDeclaration,
        input_bindings: list[WorkflowInputBinding],
    ) -> ConditionDeclaration | None:
        if declaration == RuleMatchDeclaration():
            return None
        subject = next((binding.expression for binding in input_bindings
                        if binding.name == "review_unit"), None)
        if subject is None:
            raise FlowValidationError(
                "Rule matching requires an explicit 'review_unit' input binding"
            )
        conditions = [
            *self._selection_compiler.compile(
                f"{subject.value}.applicability.file_extension",
                declaration.file_extensions.included,
                declaration.file_extensions.excluded,
                ConditionOperator.IN,
                ConditionOperator.NOT_IN,
            ),
            *self._selection_compiler.compile(
                f"{subject.value}.applicability.unit_kind",
                [kind.value for kind in declaration.unit_kinds.included],
                [kind.value for kind in declaration.unit_kinds.excluded],
                ConditionOperator.IN,
                ConditionOperator.NOT_IN,
            ),
            *self._selection_compiler.compile(
                f"{subject.value}.applicability.tags",
                list(declaration.tags.included),
                list(declaration.tags.excluded),
                ConditionOperator.CONTAINS,
                ConditionOperator.NOT_CONTAINS,
            ),
        ]
        return self._condition_conjoiner.conjoin(conditions)
