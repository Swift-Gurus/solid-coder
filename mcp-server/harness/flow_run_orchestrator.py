"""
solid-name: FlowRunOrchestrator
solid-category: service
solid-spec: [SPEC-031]
solid-description: Orchestrates flow runs with operations for starting, stepping, status monitoring, and lock clearing.
"""

from __future__ import annotations

from harness.active_run_lock_clearing import ActiveRunLockClearing
from harness.flow_next_result import FlowNextResult
from harness.flow_start_result import FlowStartResult
from harness.flow_starting import FlowStarting
from harness.flow_status_reading import FlowStatusReading
from harness.flow_status_result import FlowStatusResult
from harness.flow_stepping import FlowStepping


class FlowRunOrchestrator:

    def __init__(
        self,
        starter: FlowStarting,
        stepper: FlowStepping,
        status_reader: FlowStatusReading,
        lock_clearer: ActiveRunLockClearing,
    ) -> None:
        self._starter = starter
        self._stepper = stepper
        self._status_reader = status_reader
        self._lock_clearer = lock_clearer

    def flow_start(self, flow: str, params: dict | None = None, isolated: bool = False) -> FlowStartResult:
        return self._starter.flow_start(flow, params, isolated)

    def flow_next(self, outputs: dict | None = None, run_id: str | None = None) -> FlowNextResult:
        return self._stepper.flow_next(outputs, run_id)

    def flow_status(self, run_id: str | None = None) -> FlowStatusResult:
        return self._status_reader.flow_status(run_id)

    def flow_clear_lock(self, run_id: str) -> str:
        return self._lock_clearer.clear(run_id)
