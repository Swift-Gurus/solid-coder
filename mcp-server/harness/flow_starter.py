"""
solid-name: FlowStarter
solid-category: service
solid-spec: [SPEC-031]
solid-description: Starts a flow run and returns its initial ready steps or terminal outcome.
"""

from __future__ import annotations

from harness.execution_and_readiness_coordinating import ExecutionAndReadinessCoordinating
from harness.flow_initializing import FlowInitializing
from harness.flow_start_result import FlowStartResult
from harness.flow_start_result_building import FlowStartResultBuilding
from harness.flow_starting import FlowStarting


class FlowStarter(FlowStarting):
    """
    solid-description: Starts a flow run and returns its initial ready steps or terminal outcome.
    solid-category: service
    """

    def __init__(
        self,
        initializer: FlowInitializing,
        execution_and_readiness_coordinator: ExecutionAndReadinessCoordinating,
        result_builder: FlowStartResultBuilding,
    ) -> None:
        self._initializer = initializer
        self._execution_and_readiness_coordinator = execution_and_readiness_coordinator
        self._result_builder = result_builder

    def flow_start(self, flow: str, params: dict | None = None, isolated: bool = False) -> FlowStartResult:
        params = params or {}
        init = self._initializer.initialize(flow, params, isolated)
        outcome = self._execution_and_readiness_coordinator.coordinate(
            init.effective_base_dir, init.location.run_id, init.location.events_path, init.flow_def, params
        )
        return self._result_builder.build(init.location.run_id, outcome, isolated)
