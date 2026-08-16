"""Defines workflow runtime-context construction."""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: RunContextBuilding
solid-category: abstraction
solid-spec: [SPEC-031, SPEC-037]
solid-description: Contract for building typed workflow runtime context from run state and parameters.
"""
class RunContextBuilding(Protocol):

    def build(self, params: dict, run_state: RunState) -> WorkflowRunContext: ...
