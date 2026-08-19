"""Runs operation workflows through the real flow-engine composition root."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.flow_next_result import FlowNextResult
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.flow_start_result import FlowStartResult
from harness.operation_registration import OperationRegistration
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: OperationWorkflowIntegrationDriver
solid-category: test-support
solid-spec: [SPEC-010, SPEC-040]
solid-description: Reuses real flow-engine setup for logical-operation integration scenarios.
"""
class OperationWorkflowIntegrationDriver:
    def __init__(
        self,
        project_root: Path,
        registrations: list[OperationRegistration],
    ) -> None:
        self.project_root = project_root
        self.workflow_path = project_root / "workflow.yaml"
        self._registrations = registrations

    def write_workflow(self, declaration: str) -> None:
        self.workflow_path.write_text(declaration, encoding="utf-8")

    def start(
        self,
        params: dict[str, Any] | None = None,
    ) -> FlowStartResult:
        return self._orchestrator().flow_start(
            str(self.workflow_path),
            params=params,
        )

    def advance(
        self,
        outputs: dict[str, Any] | None = None,
    ) -> FlowNextResult:
        return self._orchestrator().flow_next(outputs)

    def _orchestrator(self):
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
            operation_registrations=self._registrations,
        ).build()
