"""Defines parsing of workflow-include runtime controls."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from harness.workflow_include_runtime import WorkflowIncludeRuntime


"""
solid-name: WorkflowIncludeRuntimeParsing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for mapping include-boundary fields into typed runtime controls.
"""
class WorkflowIncludeRuntimeParsing(Protocol):
    def parse(
        self,
        raw: Mapping[str, object],
        policy_source: Mapping[str, object] | None = None,
    ) -> WorkflowIncludeRuntime: ...
