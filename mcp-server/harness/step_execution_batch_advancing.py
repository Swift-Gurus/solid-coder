"""Defines persistence and failure handling for engine-owned execution batches."""

from __future__ import annotations

from typing import Protocol

from harness.ready_step_execution_outcome import ReadyStepExecutionOutcome
from harness.step_execution_batch_request import StepExecutionBatchRequest


"""
solid-name: StepExecutionBatchAdvancing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for validating and advancing a correlated engine-owned workflow-step batch.
"""
class StepExecutionBatchAdvancing(Protocol):
    def advance(
        self,
        request: StepExecutionBatchRequest,
    ) -> ReadyStepExecutionOutcome: ...
