"""Collects authored references from typed workflow conditions."""

from functools import singledispatchmethod

from harness.all_condition import AllCondition
from harness.any_condition import AnyCondition
from harness.comparison_condition import ComparisonCondition
from harness.condition_declaration import ConditionDeclaration
from harness.condition_reference_collecting import ConditionReferenceCollecting
from harness.not_condition import NotCondition
from harness.workflow_expression import WorkflowExpression

"""
solid-name: ConditionReferenceCollector
solid-category: service
solid-spec: [SPEC-053]
solid-description: Collects authored references across the sealed workflow condition family.
"""


class ConditionReferenceCollector(ConditionReferenceCollecting):
    @singledispatchmethod
    def collect(
        self,
        condition: ConditionDeclaration,
    ) -> list[WorkflowExpression]:
        return []

    @collect.register(ComparisonCondition)
    def _collect_comparison(
        self,
        condition: ComparisonCondition,
    ) -> list[WorkflowExpression]:
        return [condition.reference]

    @collect.register(AllCondition)
    def _collect_all(self, condition: AllCondition) -> list[WorkflowExpression]:
        return self._collect_many(condition.conditions)

    @collect.register(AnyCondition)
    def _collect_any(self, condition: AnyCondition) -> list[WorkflowExpression]:
        return self._collect_many(condition.conditions)

    @collect.register(NotCondition)
    def _collect_not(self, condition: NotCondition) -> list[WorkflowExpression]:
        return self.collect(condition.condition)

    def _collect_many(
        self,
        conditions: tuple[ConditionDeclaration, ...],
    ) -> list[WorkflowExpression]:
        return [
            reference
            for condition in conditions
            for reference in self.collect(condition)
        ]
