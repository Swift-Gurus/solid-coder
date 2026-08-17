"""Resolves workflow iteration expressions into ordered item collections."""

from __future__ import annotations

from typing import Any

from harness.for_each_items_resolving import ForEachItemsResolving
from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_resolving import StepOutputReferenceResolving
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ForEachItemsResolver
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Resolves and validates workflow for-each expressions as ordered item collections.
"""
class ForEachItemsResolver(ForEachItemsResolving):
    def __init__(
        self,
        reference_resolver: StepOutputReferenceResolving[list[Any]],
    ) -> None:
        self._reference_resolver = reference_resolver

    def resolve(
        self,
        step_id: str,
        reference: StepOutputReference,
        context: WorkflowRunContext,
    ) -> list[Any]:
        return self._reference_resolver.resolve(reference, context)
