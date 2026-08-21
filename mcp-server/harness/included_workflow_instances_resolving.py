"""Defines discovery of materialized included-workflow instances."""

from __future__ import annotations

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import FlowDef


"""
solid-name: IncludedWorkflowInstancesResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving the ordered materialized instances owned by an include alias.
"""
class IncludedWorkflowInstancesResolving(Protocol):
    def resolve(
        self,
        flow: FlowDef,
        alias: str,
    ) -> list[IncludedWorkflowInstance]: ...
