"""Resolves workflow iteration expressions into ordered item collections."""

from __future__ import annotations

from typing import Any, cast

from harness.collection_source_reference import CollectionSourceReference
from harness.expression_evaluating import ExpressionEvaluating
from harness.for_each_items_resolving import ForEachItemsResolving
from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_resolving import StepOutputReferenceResolving
from harness.workflow_output_reference import WorkflowOutputReference
from harness.workflow_run_context import WorkflowRunContext

"""
solid-name: ForEachItemsResolver
solid-category: service
solid-spec: [SPEC-010, SPEC-030, SPEC-056]
solid-description: Resolves typed step outputs and projected child-workflow outputs into ordered item collections.
"""


class ForEachItemsResolver(ForEachItemsResolving):
    def __init__(
        self,
        reference_resolver: StepOutputReferenceResolving[list[Any]],
        expression_evaluator: ExpressionEvaluating,
    ) -> None:
        self._reference_resolver = reference_resolver
        self._expression_evaluator = expression_evaluator

    def resolve(
        self,
        step_id: str,
        reference: CollectionSourceReference,
        context: WorkflowRunContext,
    ) -> list[Any]:
        if isinstance(reference, StepOutputReference):
            if context.skipped_steps.find(reference.step_id).present:
                return []
            return self._reference_resolver.resolve(reference, context)
        return cast(
            list[Any],
            self._expression_evaluator.evaluate(
                self._workflow_expression(reference),
                context,
            ),
        )

    @staticmethod
    def _workflow_expression(reference: WorkflowOutputReference) -> str:
        return f"workflows.{reference.workflow_alias}.outputs.{reference.output_name}"
