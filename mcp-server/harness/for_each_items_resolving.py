"""Defines resolution of workflow iteration items."""

from __future__ import annotations

from typing import Any, Protocol

from harness.collection_source_reference import CollectionSourceReference
from harness.workflow_run_context import WorkflowRunContext

"""
solid-name: ForEachItemsResolving
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-030, SPEC-056]
solid-description: Contract for resolving a typed step or child-workflow source into an ordered item collection.
"""


class ForEachItemsResolving(Protocol):
    def resolve(
        self,
        step_id: str,
        reference: CollectionSourceReference,
        context: WorkflowRunContext,
    ) -> list[Any]: ...
