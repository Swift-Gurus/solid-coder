"""Advances workflow runs from submitted step outputs."""

from __future__ import annotations

from pathlib import Path

from harness.attempt_failure_handling import AttemptFailureHandling
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, StepInstance
from harness.output_recording import OutputRecording
from harness.session_id_reading import SessionIdReading
from harness.step_handler_resolving import StepHandlerResolving
from harness.step_output_submission_mapping import StepOutputSubmissionMapping
from harness.submission_outcome import SubmissionOutcome
from harness.turn_advancing import TurnAdvancing


"""
solid-name: OutputSubmissionAdvancer
solid-description: Advances a workflow run from validated step-instance output submissions.
solid-category: service
solid-spec: [SPEC-010, SPEC-031]
"""
class OutputSubmissionAdvancer:

    def __init__(
        self,
        step_handler_resolver: StepHandlerResolving,
        attempt_failure_handler: AttemptFailureHandling,
        session_reader: SessionIdReading,
        output_recorder: OutputRecording,
        turn_advancer: TurnAdvancing,
        submission_mapper: StepOutputSubmissionMapping,
    ) -> None:
        self._step_handler_resolver = step_handler_resolver
        self._attempt_failure_handler = attempt_failure_handler
        self._session_reader = session_reader
        self._output_recorder = output_recorder
        self._turn_advancer = turn_advancer
        self._submission_mapper = submission_mapper

    def submit(
        self,
        events_path: str,
        base_dir: Path,
        run_id: str,
        ready: list[StepInstance],
        step_outputs: dict,
        flow_def: FlowDef,
    ) -> SubmissionOutcome:
        mapping = self._submission_mapper.map(ready, step_outputs)
        if mapping.error is not None:
            return SubmissionOutcome(
                terminal=FlowNextResult(status="ready", error=mapping.error)
            )
        step_outputs = mapping.outputs
        ready_ids = {instance.instance_id for instance in ready}
        non_current_ids = sorted(set(step_outputs) - ready_ids)
        if non_current_ids:
            submitted_id = non_current_ids[0]
            return SubmissionOutcome(
                terminal=FlowNextResult(
                    status="ready",
                    error=(
                        f"Rejected: step instance '{submitted_id}' is not currently ready. "
                        "Submit only an id returned by the latest flow_start or flow_next response."
                    ),
                )
            )

        step_map = {step.id: step for step in flow_def.steps}
        addressed = [instance for instance in ready if instance.instance_id in step_outputs]
        valid_instances: list[StepInstance] = []
        valid_outputs: dict = {}

        for instance in addressed:
            step_def = step_map[instance.step_id]
            handler = self._step_handler_resolver.resolve(step_def.type)
            validation = handler.validate(instance, step_outputs[instance.instance_id], flow_def)
            if validation.ok:
                valid_instances.append(instance)
                valid_outputs[instance.instance_id] = step_outputs[instance.instance_id]
                continue

            terminal = self._attempt_failure_handler.handle(
                step_id=instance.step_id,
                reason="; ".join(validation.errors),
                reopen=False,
                base_dir=base_dir,
                run_id=run_id,
                events_path=events_path,
                flow_def=flow_def,
                attempt_id=instance.instance_id,
            )
            if terminal is not None:
                return SubmissionOutcome(terminal=terminal)

        if not valid_instances:
            return SubmissionOutcome()

        session_id = self._session_reader.read_session_id()
        self._output_recorder.record(events_path, ready, valid_outputs, session_id)
        run_state = self._turn_advancer.advance(events_path)
        return SubmissionOutcome(run_state=run_state)
