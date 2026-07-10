"""
solid-name: flow_run_orchestrator_fixtures
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Provides test double fixtures for orchestration service dependencies.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from harness.active_run_exists_error import ActiveRunExistsError
from harness.models import FlowDef, RunState, StepInstance, StepOutputs
from harness.run_metadata import RunMetadata
from harness.step_result import StepResult


class StubFlowLoader:
    def __init__(self, flow_def: FlowDef) -> None:
        self._flow_def = flow_def

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        return self._flow_def


class SpyActiveRunPointer:
    def __init__(self, initial_run_id: str = "") -> None:
        self._run_id = initial_run_id
        self.written: list[str] = []
        self.deleted = False

    def read(self, base_dir: Path) -> str:
        if not self._run_id:
            raise FileNotFoundError("No active run")
        return self._run_id

    def write(self, base_dir: Path, run_id: str) -> None:
        if self._run_id:
            raise ActiveRunExistsError(self._run_id)
        self._run_id = run_id
        self.written.append(run_id)

    def delete(self, base_dir: Path) -> None:
        self._run_id = ""
        self.deleted = True


class StubScaffolder:
    def __init__(self, run_dir: Path) -> None:
        self._run_dir = run_dir

    def scaffold(self, base_dir: Path, run_id: str, flow_def: FlowDef) -> Path:
        self._run_dir.mkdir(parents=True, exist_ok=True)
        return self._run_dir


class SpyEventAppender:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict]] = []

    def append(self, path: str, event_type: str, payload: dict) -> None:
        self.events.append((path, event_type, payload))


class StubEventLog:
    def __init__(self, run_states: list[RunState] | None = None) -> None:
        self._states = list(run_states or [])
        self._call_count = 0

    def replay(self, path: str) -> RunState:
        if self._call_count < len(self._states):
            state = self._states[self._call_count]
            self._call_count += 1
            return state
        return RunState(completed={}, running=[], turn_count=0, status="in_progress")

    def append(self, path: str, event_type: str, payload: dict) -> None:
        pass


class StubDAGRunner:
    def __init__(self, step_sequences: list[list[StepInstance]]) -> None:
        self._sequences = list(step_sequences)
        self._call_count = 0

    def ready_steps(self, flow_def: FlowDef, run_state: RunState, context: dict) -> list[StepInstance]:
        if self._call_count < len(self._sequences):
            steps = self._sequences[self._call_count]
            self._call_count += 1
            return steps
        return []


class StubOutputValidator:
    def __init__(self, errors: list[str] | None = None) -> None:
        self._errors = errors or []

    def validate(self, ready: list, outputs: dict, flow_def: FlowDef) -> list[str]:
        return self._errors


class StubStepResultBuilder:
    def build(self, instances: list[StepInstance], flow_def: FlowDef, detected_env: str) -> list[StepResult]:
        return [
            StepResult(
                step_id=i.step_id,
                instance_id=i.instance_id,
                prompt=i.prompt,
                execution={"mode": "inline"},
            )
            for i in instances
        ]


class CapturingStepResultBuilder:
    def __init__(self) -> None:
        self.captured_instances: list[StepInstance] = []

    def build(self, instances: list[StepInstance], flow_def: FlowDef, detected_env: str) -> list[StepResult]:
        self.captured_instances.extend(instances)
        return [
            StepResult(
                step_id=i.step_id,
                instance_id=i.instance_id,
                prompt=i.prompt,
                execution={"mode": "inline"},
            )
            for i in instances
        ]


class StubSessionReader:
    def __init__(self, session_id: str = "session-42") -> None:
        self._session_id = session_id

    def read_session_id(self) -> str:
        return self._session_id


class StubSearchPaths:
    def resolve(self) -> list[Path]:
        return []


class SpyMetadataStore:
    def __init__(self, metadata: RunMetadata | None = None) -> None:
        self._metadata = metadata or RunMetadata(params={}, detected_env="")
        self.written: list[RunMetadata] = []

    def write(self, run_dir: Path, metadata: RunMetadata) -> None:
        self.written.append(metadata)

    def read(self, run_dir: Path) -> RunMetadata:
        return self._metadata


class StubEnvDetector:
    def __init__(self, env: str = "") -> None:
        self._env = env

    def detect(self) -> str:
        return self._env


class StubContextBuilder:
    def build(self, params: dict, run_state: RunState) -> dict:
        return {"params": params}


class StubBaseDirResolver:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def resolve(self) -> Path:
        return self._base_dir
