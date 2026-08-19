"""Compiles one rule selector into workflow comparison conditions."""

from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.rule_selection_condition_compiling import (
    RuleSelectionConditionCompiling,
)
from harness.workflow_expression import WorkflowExpression


"""
solid-name: RuleSelectionConditionCompiler
solid-category: service
solid-spec: [SPEC-039]
solid-description: Translates included and excluded selector values into typed comparison clauses.
"""
class RuleSelectionConditionCompiler(RuleSelectionConditionCompiling):
    def compile(
        self,
        reference: str,
        included: list[object],
        excluded: list[object],
        inclusion_operator: ConditionOperator,
        exclusion_operator: ConditionOperator,
    ) -> list[ComparisonCondition]:
        included_values = (
            [included]
            if inclusion_operator is ConditionOperator.IN and included
            else included
        )
        excluded_values = (
            [excluded]
            if exclusion_operator is ConditionOperator.NOT_IN and excluded
            else excluded
        )
        conditions = [
            ComparisonCondition(
                reference=WorkflowExpression(reference),
                operator=inclusion_operator,
                expected=value,
            )
            for value in included_values
        ]
        conditions.extend(
            ComparisonCondition(
                reference=WorkflowExpression(reference),
                operator=exclusion_operator,
                expected=value,
            )
            for value in excluded_values
        )
        return conditions
