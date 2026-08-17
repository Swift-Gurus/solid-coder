"""Defines the shared marker for declarative workflow conditions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from harness.condition_evidence import ConditionEvidence
from harness.condition_runtime import ConditionRuntime
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionDeclaration
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for defining typed workflow conditions used by conditional execution.
"""
class ConditionDeclaration(ABC):
    __slots__ = ()

    @abstractmethod
    def evaluate(
        self,
        runtime: ConditionRuntime,
        context: WorkflowRunContext,
    ) -> ConditionEvidence:
        raise NotImplementedError
