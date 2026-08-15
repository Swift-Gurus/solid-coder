"""
solid-name: test_engine_step_drainer
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests automatically driving ready script steps to completion or failure before control returns to the calling agent, leaving agent steps untouched.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.engine_step_drainer import EngineStepDrainer
from harness.flow_next_result import FlowNextResult
from harness.models import FlowDef, RunState, StepDef, StepInstance, StepOutputs
from harness.ready_step_executor import ReadyStepExecutor
from harness.run_snapshot import RunSnapshot
from harness.step_execution_failure_handler import StepExecutionFailureHandler
from harness.step_run_outcome import StepRunOutcome
from harness.step_skip import StepSkip
from harness.workflow_condition_gate_result import WorkflowConditionGateResult


class ScriptedRunSnapshotResolver:
    def __init__(self, snapshots: list[RunSnapshot]) -> None:
        self._snapshots = list(snapshots)
        self.call_count = 0

    def resolve(self, events_path, flow_def, params) -> RunSnapshot:
        snapshot = self._snapshots[min(self.call_count, len(self._snapshots) - 1)]
        self.call_count += 1
        return snapshot


class ScriptedHandlerResolver:
    def __init__(self, handlers: dict) -> None:
        self._handlers = handlers

    def resolve(self, step_type: str):
        return self._handlers[step_type]


class StubHandler:
    def __init__(self, outcome: StepRunOutcome) -> None:
        self._outcome = outcome

    def run(self, instance, step_def) -> StepRunOutcome:
        return self._outcome


class SpyOutputRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def record(self, events_path, ready, step_outputs, session_id) -> None:
        self.calls.append((events_path, ready, step_outputs, session_id))


class SpyStepSkipRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def record(self, events_path, ready) -> None:
        self.calls.append((events_path, ready))


class ScriptedWorkflowConditionGate:
    def __init__(self, results: list[WorkflowConditionGateResult]) -> None:
        self._results = results
        self.calls = []

    def advance(self, events_path, flow_def, params, run_state):
        self.calls.append((events_path, flow_def, params, run_state))
        index = min(len(self.calls) - 1, len(self._results) - 1)
        return self._results[index]


class SpyAttemptFailureHandler:
    def __init__(self, result) -> None:
        self._result = result
        self.calls: list[dict] = []

    def handle(self, **kwargs):
        self.calls.append(kwargs)
        return self._result


class ExhaustsAfterAttemptFailureHandler:
    def __init__(self, attempts_before_exhaustion: int, terminal: FlowNextResult) -> None:
        self._remaining = attempts_before_exhaustion
        self._terminal = terminal
        self.calls: list[dict] = []

    def handle(self, **kwargs):
        self.calls.append(kwargs)
        self._remaining -= 1
        return self._terminal if self._remaining <= 0 else None


class StubFailureAttributor:
    def __init__(self, target: str) -> None:
        self._target = target

    def attribute(self, failed_step, run_state, flow_def) -> str:
        return self._target


def _run_state() -> RunState:
    return RunState(completed={}, running=[], turn_count=0, status="in_progress")


class EngineStepDrainerFactory:
    """Builds an EngineStepDrainer with sensible stub and spy defaults."""

    def __init__(self) -> None:
        self.run_snapshot_resolver = ScriptedRunSnapshotResolver([RunSnapshot(run_state=_run_state(), ready=[])])
        self.workflow_condition_gate = ScriptedWorkflowConditionGate([
            WorkflowConditionGateResult(progressed=False, allows_execution=True)
        ])
        self.step_handler_resolver = ScriptedHandlerResolver({})
        self.failure_attributor = StubFailureAttributor("")
        self.attempt_failure_handler = SpyAttemptFailureHandler(None)
        self.output_recorder = SpyOutputRecorder()
        self.step_skip_recorder = SpyStepSkipRecorder()

    def with_run_snapshot_resolver(self, resolver) -> "EngineStepDrainerFactory":
        self.run_snapshot_resolver = resolver
        return self

    def with_step_handler_resolver(self, resolver) -> "EngineStepDrainerFactory":
        self.step_handler_resolver = resolver
        return self

    def with_workflow_condition_gate(self, gate) -> "EngineStepDrainerFactory":
        self.workflow_condition_gate = gate
        return self

    def with_failure_attributor(self, attributor) -> "EngineStepDrainerFactory":
        self.failure_attributor = attributor
        return self

    def with_attempt_failure_handler(self, handler) -> "EngineStepDrainerFactory":
        self.attempt_failure_handler = handler
        return self

    def make_sut(self) -> EngineStepDrainer:
        return EngineStepDrainer(
            run_snapshot_resolver=self.run_snapshot_resolver,
            workflow_condition_gate=self.workflow_condition_gate,
            step_skip_recorder=self.step_skip_recorder,
            ready_step_executor=ReadyStepExecutor(
                step_handler_resolver=self.step_handler_resolver,
                failure_handler=StepExecutionFailureHandler(
                    failure_attributor=self.failure_attributor,
                    attempt_failure_handler=self.attempt_failure_handler,
                ),
                output_recorder=self.output_recorder,
            ),
        )


class TestEngineStepDrainer(unittest.TestCase):

    def test_replays_a_false_workflow_decision_without_executing_ready_steps(self):
        instance = StepInstance(
            step_id="review",
            instance_id="review",
            item=None,
            prompt="Never execute",
        )
        snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        condition_gate = ScriptedWorkflowConditionGate([
            WorkflowConditionGateResult(progressed=True, allows_execution=False),
            WorkflowConditionGateResult(progressed=False, allows_execution=False),
        ])
        factory = (
            EngineStepDrainerFactory()
            .with_run_snapshot_resolver(
                ScriptedRunSnapshotResolver([snapshot, snapshot])
            )
            .with_workflow_condition_gate(condition_gate)
        )

        result = factory.make_sut().run_ready(
            Path("/runs"),
            "run-1",
            "events.jsonl",
            FlowDef(
                name="conditional",
                max_turns=10,
                steps=[StepDef(id="review", prompt="Never execute")],
            ),
            {"enabled": False},
        )

        self.assertIsNone(result)
        self.assertEqual(len(condition_gate.calls), 2)
        self.assertEqual(factory.output_recorder.calls, [])
        self.assertEqual(factory.step_skip_recorder.calls, [])

    def test_replays_a_true_workflow_decision_then_executes_ready_steps(self):
        instance = StepInstance(
            step_id="prepare",
            instance_id="prepare",
            item=None,
            prompt="",
            automatic_outputs=StepOutputs(values={"ready": True}),
        )
        ready_snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        empty_snapshot = RunSnapshot(run_state=_run_state(), ready=[])
        condition_gate = ScriptedWorkflowConditionGate([
            WorkflowConditionGateResult(progressed=True, allows_execution=True),
            WorkflowConditionGateResult(progressed=False, allows_execution=True),
        ])
        factory = (
            EngineStepDrainerFactory()
            .with_run_snapshot_resolver(
                ScriptedRunSnapshotResolver(
                    [ready_snapshot, ready_snapshot, empty_snapshot]
                )
            )
            .with_workflow_condition_gate(condition_gate)
        )

        result = factory.make_sut().run_ready(
            Path("/runs"),
            "run-1",
            "events.jsonl",
            FlowDef(
                name="conditional",
                max_turns=10,
                steps=[StepDef(id="prepare", prompt="")],
            ),
            {"enabled": True},
        )

        self.assertIsNone(result)
        self.assertEqual(len(condition_gate.calls), 3)
        self.assertEqual(len(factory.output_recorder.calls), 1)

    def test_records_skipped_instances_before_invoking_an_executor(self):
        condition = ComparisonCondition(
            reference="{{params.enabled}}",
            operator=ConditionOperator.EQUALS,
            expected=True,
        )
        skip = StepSkip(
            step_id="conditional",
            instance_id="conditional-1",
            condition=condition,
        )
        instance = StepInstance(
            step_id="conditional",
            instance_id="conditional-1",
            item=None,
            prompt="Never execute",
            skip=skip,
        )
        first_snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        second_snapshot = RunSnapshot(run_state=_run_state(), ready=[])
        factory = EngineStepDrainerFactory().with_run_snapshot_resolver(
            ScriptedRunSnapshotResolver([first_snapshot, second_snapshot])
        )

        result = factory.make_sut().run_ready(
            Path("/runs"),
            "run-1",
            "events.jsonl",
            FlowDef(
                name="f",
                max_turns=10,
                steps=[StepDef(id="conditional", prompt="Never execute")],
            ),
            {},
        )

        self.assertIsNone(result)
        self.assertEqual(
            factory.step_skip_recorder.calls,
            [("events.jsonl", [instance])],
        )
        self.assertEqual(factory.output_recorder.calls, [])

    def test_records_engine_outputs_without_resolving_a_handler(self):
        automatic_outputs = StepOutputs(values={"result": []})
        instance = StepInstance(
            step_id="review",
            instance_id="review-0",
            item=None,
            prompt="",
            iteration_index=0,
            automatic_outputs=automatic_outputs,
        )
        first_snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        second_snapshot = RunSnapshot(run_state=_run_state(), ready=[])
        flow_def = FlowDef(
            name="f",
            max_turns=10,
            steps=[StepDef(id="review", prompt="", type="agent")],
        )
        factory = EngineStepDrainerFactory().with_run_snapshot_resolver(
            ScriptedRunSnapshotResolver([first_snapshot, second_snapshot])
        )

        result = factory.make_sut().run_ready(
            Path("/runs"),
            "run-1",
            "events.jsonl",
            flow_def,
            {},
        )

        self.assertIsNone(result)
        self.assertEqual(
            factory.output_recorder.calls,
            [("events.jsonl", [instance], {"review-0": {"result": []}}, "engine")],
        )

    def test_returns_none_when_only_agent_steps_are_ready(self):
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p", type="agent")])
        sut = EngineStepDrainerFactory().with_run_snapshot_resolver(
            ScriptedRunSnapshotResolver([snapshot])
        ).with_step_handler_resolver(
            ScriptedHandlerResolver({"agent": StubHandler(StepRunOutcome(awaiting_input=True))})
        ).with_failure_attributor(StubFailureAttributor("a")).make_sut()

        result = sut.run_ready(Path("/runs"), "run-1", "events.jsonl", flow_def, {})

        self.assertIsNone(result)

    def test_records_outputs_for_a_successful_script_step_and_stops_when_nothing_more_is_ready(self):
        instance = StepInstance(step_id="s", instance_id="s-1", item=None, prompt="")
        first_snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        second_snapshot = RunSnapshot(run_state=_run_state(), ready=[])
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="s", prompt="", type="script", command=["run.sh"])])
        factory = EngineStepDrainerFactory().with_run_snapshot_resolver(
            ScriptedRunSnapshotResolver([first_snapshot, second_snapshot])
        ).with_step_handler_resolver(ScriptedHandlerResolver({
            "script": StubHandler(StepRunOutcome(awaiting_input=False, outputs={"x": 1})),
        })).with_failure_attributor(StubFailureAttributor("s"))

        result = factory.make_sut().run_ready(Path("/runs"), "run-1", "events.jsonl", flow_def, {})

        self.assertIsNone(result)
        self.assertEqual(factory.output_recorder.calls, [("events.jsonl", [instance], {"s-1": {"x": 1}}, "engine")])

    def test_delegates_failure_to_attempt_failure_handler_and_returns_its_terminal_result(self):
        instance = StepInstance(step_id="s", instance_id="s-1", item=None, prompt="")
        snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="s", prompt="", type="script", command=["run.sh"])])
        terminal = FlowNextResult(status="failed")
        failure_handler = SpyAttemptFailureHandler(terminal)
        sut = EngineStepDrainerFactory().with_run_snapshot_resolver(
            ScriptedRunSnapshotResolver([snapshot])
        ).with_step_handler_resolver(ScriptedHandlerResolver({
            "script": StubHandler(StepRunOutcome(awaiting_input=False, rejection_reason="boom")),
        })).with_failure_attributor(StubFailureAttributor("s")).with_attempt_failure_handler(failure_handler).make_sut()

        result = sut.run_ready(Path("/runs"), "run-1", "events.jsonl", flow_def, {})

        self.assertIs(result, terminal)
        self.assertEqual(failure_handler.calls, [{
            "step_id": "s", "reason": "boom", "reopen": False,
            "base_dir": Path("/runs"), "run_id": "run-1", "events_path": "events.jsonl", "flow_def": flow_def,
            "attempt_id": "s-1",
        }])

    def test_retries_a_failing_script_step_internally_until_attempts_are_exhausted(self):
        instance = StepInstance(step_id="s", instance_id="s-1", item=None, prompt="")
        snapshot_with_ready = RunSnapshot(run_state=_run_state(), ready=[instance])
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="s", prompt="", type="script", command=["run.sh"])])
        terminal = FlowNextResult(status="failed")
        failure_handler = ExhaustsAfterAttemptFailureHandler(attempts_before_exhaustion=3, terminal=terminal)
        sut = EngineStepDrainerFactory().with_run_snapshot_resolver(
            ScriptedRunSnapshotResolver([snapshot_with_ready])
        ).with_step_handler_resolver(ScriptedHandlerResolver({
            "script": StubHandler(StepRunOutcome(awaiting_input=False, rejection_reason="boom")),
        })).with_failure_attributor(StubFailureAttributor("s")).with_attempt_failure_handler(failure_handler).make_sut()

        result = sut.run_ready(Path("/runs"), "run-1", "events.jsonl", flow_def, {})

        self.assertIs(result, terminal)
        self.assertEqual(len(failure_handler.calls), 3)

    def test_reopens_an_upstream_agent_step_attributed_by_the_failure_attributor(self):
        instance = StepInstance(step_id="s", instance_id="s-1", item=None, prompt="")
        snapshot = RunSnapshot(run_state=_run_state(), ready=[instance])
        flow_def = FlowDef(name="f", max_turns=10, steps=[
            StepDef(id="writer", prompt="p", type="agent"),
            StepDef(id="s", prompt="", type="script", command=["run.sh"], depends_on=["writer"]),
        ])
        failure_handler = ExhaustsAfterAttemptFailureHandler(attempts_before_exhaustion=1, terminal=FlowNextResult(status="failed"))
        sut = EngineStepDrainerFactory().with_run_snapshot_resolver(
            ScriptedRunSnapshotResolver([snapshot])
        ).with_step_handler_resolver(ScriptedHandlerResolver({
            "script": StubHandler(StepRunOutcome(awaiting_input=False, rejection_reason="bad output")),
        })).with_failure_attributor(StubFailureAttributor("writer")).with_attempt_failure_handler(failure_handler).make_sut()

        sut.run_ready(Path("/runs"), "run-1", "events.jsonl", flow_def, {})

        self.assertEqual(failure_handler.calls[0]["step_id"], "writer")
        self.assertTrue(failure_handler.calls[0]["reopen"])


if __name__ == "__main__":
    unittest.main()
