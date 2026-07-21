"""
solid-name: FlowRunOrchestrator
solid-category: service
solid-spec: [SPEC-013]
solid-description: Orchestrates flow runs by exposing operations for starting, stepping, and status monitoring.
"""

from __future__ import annotations

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
    ) -> None:
        self._starter = starter
        self._stepper = stepper
        self._status_reader = status_reader

    def flow_start(self, flow: str, params: dict | None = None) -> FlowStartResult:
        return self._starter.flow_start(flow, params)

    def flow_next(self, outputs: dict | None = None) -> FlowNextResult:
        return self._stepper.flow_next(outputs)

    def flow_status(self) -> FlowStatusResult:
        return self._status_reader.flow_status()
