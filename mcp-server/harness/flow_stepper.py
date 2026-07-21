"""
solid-name: FlowStepper
solid-category: service
solid-spec: [SPEC-013]
solid-description: Validates step outputs and advances the flow to the next step.
"""

from __future__ import annotations

from harness.active_run_locating import ActiveRunLocating
from harness.flow_loading import FlowLoading
from harness.flow_next_result import FlowNextResult
from harness.flow_stepping import FlowStepping
from harness.output_recording import OutputRecording
from harness.run_completion_checking import RunCompletionChecking
from harness.run_metadata_persisting import RunMetadataPersisting
from harness.run_snapshot_resolving import RunSnapshotResolving
from harness.session_id_reading import SessionIdReading
from harness.step_output_validating import StepOutputValidating
from harness.step_result_building import StepResultBuilding
from harness.turn_advancing import TurnAdvancing


class FlowStepper(FlowStepping):

    def __init__(
        self,
        run_locator: ActiveRunLocating,
        metadata_store: RunMetadataPersisting,
        flow_loader: FlowLoading,
        run_snapshot_resolver: RunSnapshotResolving,
        output_validator: StepOutputValidating,
        session_reader: SessionIdReading,
        output_recorder: OutputRecording,
        turn_advancer: TurnAdvancing,
        completion_checker: RunCompletionChecking,
        step_result_builder: StepResultBuilding,
    ) -> None:
        self._run_locator = run_locator
        self._metadata_store = metadata_store
        self._flow_loader = flow_loader
        self._run_snapshot_resolver = run_snapshot_resolver
        self._output_validator = output_validator
        self._session_reader = session_reader
        self._output_recorder = output_recorder
        self._turn_advancer = turn_advancer
        self._completion_checker = completion_checker
        self._step_result_builder = step_result_builder

    def flow_next(self, outputs: dict | None = None) -> FlowNextResult:
        location = self._run_locator.locate()
        metadata = self._metadata_store.read(location.run_dir)
        flow_def = self._flow_loader.load(location.workflow_path, [])
        snapshot = self._run_snapshot_resolver.resolve(location.events_path, flow_def, metadata.params)

        step_outputs = outputs or {}
        errors = self._output_validator.validate(snapshot.ready, step_outputs, flow_def)
        if errors:
            return FlowNextResult(status="ready", error="Output validation failed", validation_errors=errors)

        session_id = self._session_reader.read_session_id()
        self._output_recorder.record(location.events_path, snapshot.ready, step_outputs, session_id)

        run_state = self._turn_advancer.advance(location.events_path)

        terminal = self._completion_checker.check(
            location.base_dir, location.run_id, location.events_path, flow_def, run_state
        )
        if terminal is not None:
            return terminal

        next_snapshot = self._run_snapshot_resolver.resolve(location.events_path, flow_def, metadata.params)
        steps = self._step_result_builder.build(next_snapshot.ready, flow_def, metadata.detected_env)
        return FlowNextResult(status="ready", steps=steps)
