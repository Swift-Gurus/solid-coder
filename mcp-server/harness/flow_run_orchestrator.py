"""
solid-name: FlowRunOrchestrator
solid-category: service
solid-spec: [SPEC-013]
solid-description: Orchestrates flow execution from initialization through completion, tracking run state and determining ready steps.
"""

from __future__ import annotations

import uuid

from harness.active_run_pointer_storing import ActiveRunPointerStoring
from harness.dag_running import DAGRunning
from harness.env_detecting import EnvDetecting
from harness.event_appender import EventAppending
from harness.event_logging import EventLogging
from harness.flow_loading import FlowLoading
from harness.flow_next_result import FlowNextResult
from harness.flow_run_orchestrating import FlowRunOrchestrating
from harness.flow_search_path_resolving import FlowSearchPathResolving
from harness.flow_start_result import FlowStartResult
from harness.flow_status_result import FlowStatusResult
from harness.run_context_building import RunContextBuilding
from harness.run_directory_scaffolding import RunDirectoryScaffolding
from harness.run_metadata import RunMetadata
from harness.run_metadata_persisting import RunMetadataPersisting
from harness.runs_base_dir_resolving import RunsBaseDirResolving
from harness.session_id_reading import SessionIdReading
from harness.step_output_validating import StepOutputValidating
from harness.step_result_building import StepResultBuilding


class FlowRunOrchestrator:

    def __init__(
        self,
        flow_loader: FlowLoading,
        active_run: ActiveRunPointerStoring,
        scaffolder: RunDirectoryScaffolding,
        event_log: EventLogging,
        event_appender: EventAppending,
        dag_runner: DAGRunning,
        output_validator: StepOutputValidating,
        step_result_builder: StepResultBuilding,
        session_reader: SessionIdReading,
        search_paths: FlowSearchPathResolving,
        metadata_store: RunMetadataPersisting,
        env_detector: EnvDetecting,
        context_builder: RunContextBuilding,
        base_dir_resolver: RunsBaseDirResolving,
    ) -> None:
        self._flow_loader = flow_loader
        self._active_run = active_run
        self._scaffolder = scaffolder
        self._event_log = event_log
        self._event_appender = event_appender
        self._dag_runner = dag_runner
        self._output_validator = output_validator
        self._step_result_builder = step_result_builder
        self._session_reader = session_reader
        self._search_paths = search_paths
        self._metadata_store = metadata_store
        self._env_detector = env_detector
        self._context_builder = context_builder
        self._base_dir_resolver = base_dir_resolver

    def flow_start(self, flow: str, params: dict | None = None) -> FlowStartResult:
        params = params or {}
        detected_env = self._env_detector.detect()

        search_path_list = self._search_paths.resolve()
        flow_def = self._flow_loader.load(flow, [str(p) for p in search_path_list])

        base_dir = self._base_dir_resolver.resolve()
        run_id = uuid.uuid4().hex
        self._active_run.write(base_dir, run_id)

        run_dir = self._scaffolder.scaffold(base_dir, run_id, flow_def)
        self._metadata_store.write(run_dir, RunMetadata(params=params, detected_env=detected_env))

        events_path = str(run_dir / "events.jsonl")
        self._event_appender.append(events_path, "run_started", {"run_id": run_id, "flow": flow_def.name})

        run_state = self._event_log.replay(events_path)
        context = self._context_builder.build(params, run_state)
        ready = self._dag_runner.ready_steps(flow_def, run_state, context)
        steps = self._step_result_builder.build(ready, flow_def, detected_env)
        return FlowStartResult(run_id=run_id, steps=steps)

    def flow_next(self, outputs: dict | None = None) -> FlowNextResult:
        base_dir = self._base_dir_resolver.resolve()
        run_id = self._active_run.read(base_dir)
        run_dir = base_dir / run_id
        events_path = str(run_dir / "events.jsonl")

        metadata = self._metadata_store.read(run_dir)
        run_state = self._event_log.replay(events_path)
        flow_def = self._flow_loader.load(str(run_dir / "workflow.yaml"), [])

        context = self._context_builder.build(metadata.params, run_state)
        ready = self._dag_runner.ready_steps(flow_def, run_state, context)

        step_outputs = outputs or {}
        errors = self._output_validator.validate(ready, step_outputs, flow_def)
        if errors:
            return FlowNextResult(status="ready", error="Output validation failed", validation_errors=errors)

        session_id = self._session_reader.read_session_id()
        for instance in ready:
            instance_outputs = step_outputs.get(instance.instance_id, {})
            self._event_appender.append(events_path, "step_completed", {
                "instance_id": instance.instance_id,
                "step_id": instance.step_id,
                "outputs": instance_outputs,
                "session_id": session_id,
            })
            self._event_appender.append(events_path, "session_step_recorded", {
                "session_id": session_id,
                "instance_id": instance.instance_id,
            })

        run_state = self._event_log.replay(events_path)
        turn_count = run_state.turn_count + 1
        self._event_appender.append(events_path, "turn_counted", {"total": turn_count})
        run_state = self._event_log.replay(events_path)

        all_step_ids = {s.id for s in flow_def.steps}
        if all_step_ids.issubset(run_state.completed.keys()):
            self._event_appender.append(events_path, "run_completed", {"run_id": run_id})
            self._active_run.delete(base_dir)
            return FlowNextResult(status="done")

        if run_state.turn_count >= flow_def.max_turns:
            self._event_appender.append(events_path, "run_timed_out", {"run_id": run_id})
            self._active_run.delete(base_dir)
            return FlowNextResult(status="timed_out")

        context = self._context_builder.build(metadata.params, run_state)
        next_ready = self._dag_runner.ready_steps(flow_def, run_state, context)
        steps = self._step_result_builder.build(next_ready, flow_def, metadata.detected_env)
        return FlowNextResult(status="ready", steps=steps)

    def flow_status(self) -> FlowStatusResult:
        base_dir = self._base_dir_resolver.resolve()
        try:
            run_id = self._active_run.read(base_dir)
        except (FileNotFoundError, KeyError):
            return FlowStatusResult(
                flow="", run_id="", status="no_active_run",
                turn_count=0, max_turns=0,
                completed=[], running=[], pending=[],
            )

        run_dir = base_dir / run_id
        events_path = str(run_dir / "events.jsonl")
        run_state = self._event_log.replay(events_path)
        flow_def = self._flow_loader.load(str(run_dir / "workflow.yaml"), [])

        context = self._context_builder.build({}, run_state)
        pending = self._dag_runner.ready_steps(flow_def, run_state, context)

        return FlowStatusResult(
            flow=flow_def.name,
            run_id=run_id,
            status=run_state.status,
            turn_count=run_state.turn_count,
            max_turns=flow_def.max_turns,
            completed=list(run_state.completed.keys()),
            running=list(run_state.running),
            pending=[i.step_id for i in pending],
        )
