"""
solid-name: test_flow_run_orchestrator
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests the orchestration and lifecycle of multi-step workflow runs.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from harness.active_run_exists_error import ActiveRunExistsError
from harness.flow_next_result import FlowNextResult
from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_start_result import FlowStartResult
from harness.flow_status_result import FlowStatusResult
from harness.models import FlowDef, RunState, StepDef, StepInstance, StepOutputs
from harness.run_metadata import RunMetadata
from harness.tests.flow_run_orchestrator_fixtures import (
    CapturingStepResultBuilder,
    SpyActiveRunPointer,
    SpyEventAppender,
    SpyMetadataStore,
    StubBaseDirResolver,
    StubContextBuilder,
    StubDAGRunner,
    StubEnvDetector,
    StubEventLog,
    StubFlowLoader,
    StubOutputValidator,
    StubScaffolder,
    StubSearchPaths,
    StubSessionReader,
    StubStepResultBuilder,
)


def _make_flow(steps: list[StepDef], max_turns: int = 10) -> FlowDef:
    return FlowDef(name="test_flow", max_turns=max_turns, steps=steps)


def _make_step(step_id: str) -> StepDef:
    return StepDef(id=step_id, prompt=f"Do {step_id}")


def _make_instance(step_id: str) -> StepInstance:
    return StepInstance(step_id=step_id, instance_id=f"{step_id}-1", item=None, prompt=f"Do {step_id}")


def _empty_run_state() -> RunState:
    return RunState(completed={}, running=[], turn_count=0, status="in_progress")


def _completed_run_state(step_ids: list[str], turn_count: int = 1) -> RunState:
    return RunState(
        completed={sid: StepOutputs(values={}) for sid in step_ids},
        running=[],
        turn_count=turn_count,
        status="in_progress",
    )


class TestFlowRunOrchestrator(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.base_dir = Path(self._tmpdir) / "runs"
        self.run_dir = self.base_dir / "test-run"
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def _make_sut(
        self,
        flow_def=None,
        active_run=None,
        event_log_states=None,
        dag_sequences=None,
        output_errors=None,
        session_id="session-42",
        metadata=None,
        metadata_store=None,
        env="",
        step_result_builder=None,
    ):
        flow = flow_def or _make_flow([_make_step("step-a")])
        spy_active = active_run or SpyActiveRunPointer()
        spy_appender = SpyEventAppender()
        spy_meta = metadata_store or SpyMetadataStore(
            metadata=metadata or RunMetadata(params={}, detected_env=env)
        )
        builder = step_result_builder or StubStepResultBuilder()

        sut = FlowRunOrchestrator(
            flow_loader=StubFlowLoader(flow),
            active_run=spy_active,
            scaffolder=StubScaffolder(self.run_dir),
            event_log=StubEventLog(event_log_states or [_empty_run_state()]),
            event_appender=spy_appender,
            dag_runner=StubDAGRunner(dag_sequences or [[_make_instance("step-a")]]),
            output_validator=StubOutputValidator(output_errors),
            step_result_builder=builder,
            session_reader=StubSessionReader(session_id),
            search_paths=StubSearchPaths(),
            metadata_store=spy_meta,
            env_detector=StubEnvDetector(env),
            context_builder=StubContextBuilder(),
            base_dir_resolver=StubBaseDirResolver(self.base_dir),
        )
        return sut, spy_active, spy_appender, spy_meta

    def test_flow_start_creates_directory_and_returns_first_ready_steps(self):
        sut, spy_active, spy_appender, spy_meta = self._make_sut()

        result = sut.flow_start("test_flow")

        self.assertIsInstance(result, FlowStartResult)
        self.assertEqual(len(spy_active.written), 1)
        self.assertEqual(len(spy_meta.written), 1)
        event_types = [e[1] for e in spy_appender.events]
        self.assertIn("run_started", event_types)
        self.assertEqual(len(result.steps), 1)
        self.assertEqual(result.steps[0].step_id, "step-a")

    def test_flow_start_fails_when_active_run_exists(self):
        existing_pointer = SpyActiveRunPointer(initial_run_id="existing-run")
        sut, _, spy_appender, _ = self._make_sut(active_run=existing_pointer)

        with self.assertRaises(ActiveRunExistsError):
            sut.flow_start("test_flow")

        event_types = [e[1] for e in spy_appender.events]
        self.assertNotIn("run_started", event_types)

    def test_flow_next_with_valid_outputs_appends_events_and_returns_steps(self):
        flow = _make_flow([_make_step("step-a"), _make_step("step-b")])
        active = SpyActiveRunPointer(initial_run_id="run-123")
        states = [_empty_run_state(), _empty_run_state(), _empty_run_state()]
        sut, _, spy_appender, _ = self._make_sut(
            flow_def=flow,
            active_run=active,
            event_log_states=states,
            dag_sequences=[[_make_instance("step-a")], [_make_instance("step-b")]],
        )

        result = sut.flow_next({"step-a-1": {}})

        event_types = [e[1] for e in spy_appender.events]
        self.assertIn("step_completed", event_types)
        self.assertIn("session_step_recorded", event_types)
        self.assertIn("turn_counted", event_types)
        self.assertIsInstance(result, FlowNextResult)

    def test_flow_next_with_invalid_outputs_returns_error_no_events_appended(self):
        active = SpyActiveRunPointer(initial_run_id="run-456")
        sut, _, spy_appender, _ = self._make_sut(
            active_run=active,
            output_errors=["output.name is required"],
        )

        result = sut.flow_next({"step-a-1": {"bad": "value"}})

        self.assertIsNotNone(result.error)
        self.assertEqual(result.validation_errors, ["output.name is required"])
        self.assertEqual(spy_appender.events, [])

    def test_flow_next_returns_done_when_all_steps_complete(self):
        flow = _make_flow([_make_step("step-a")])
        active = SpyActiveRunPointer(initial_run_id="run-done")
        done_state = _completed_run_state(["step-a"], turn_count=1)
        sut, spy_active, spy_appender, _ = self._make_sut(
            flow_def=flow,
            active_run=active,
            event_log_states=[_empty_run_state(), done_state, done_state],
            dag_sequences=[[_make_instance("step-a")], []],
        )

        result = sut.flow_next()

        self.assertEqual(result.status, "done")
        self.assertTrue(spy_active.deleted)
        event_types = [e[1] for e in spy_appender.events]
        self.assertIn("run_completed", event_types)

    def test_flow_next_returns_timed_out_at_max_turns(self):
        flow = _make_flow([_make_step("step-a"), _make_step("step-b")], max_turns=1)
        active = SpyActiveRunPointer(initial_run_id="run-timed")
        timed_state = RunState(completed={}, running=[], turn_count=1, status="in_progress")
        sut, spy_active, spy_appender, _ = self._make_sut(
            flow_def=flow,
            active_run=active,
            event_log_states=[_empty_run_state(), _empty_run_state(), timed_state],
            dag_sequences=[[_make_instance("step-a")], []],
        )

        result = sut.flow_next()

        self.assertEqual(result.status, "timed_out")
        self.assertTrue(spy_active.deleted)
        event_types = [e[1] for e in spy_appender.events]
        self.assertIn("run_timed_out", event_types)

    def test_flow_status_returns_state_snapshot_with_no_side_effects(self):
        active = SpyActiveRunPointer(initial_run_id="run-status")
        sut, _, spy_appender, _ = self._make_sut(
            active_run=active,
            event_log_states=[_empty_run_state()],
            dag_sequences=[[_make_instance("step-a")]],
        )

        result = sut.flow_status()

        self.assertIsInstance(result, FlowStatusResult)
        self.assertEqual(result.run_id, "run-status")
        self.assertEqual(spy_appender.events, [])

    def test_flow_next_records_session_step_mapping(self):
        active = SpyActiveRunPointer(initial_run_id="run-session")
        states = [_empty_run_state(), _empty_run_state(), _empty_run_state()]
        sut, _, spy_appender, _ = self._make_sut(
            active_run=active,
            event_log_states=states,
            dag_sequences=[[_make_instance("step-a")], []],
            session_id="session-99",
        )

        sut.flow_next()

        session_events = [e for e in spy_appender.events if e[1] == "session_step_recorded"]
        self.assertGreaterEqual(len(session_events), 1)
        self.assertEqual(session_events[0][2]["session_id"], "session-99")
        self.assertEqual(session_events[0][2]["instance_id"], "step-a-1")

    def test_flow_next_interpolates_params_from_run_metadata(self):
        flow = _make_flow([
            StepDef(id="step-a", prompt="Complete me"),
            StepDef(id="step-b", prompt="Hello {{params.key}}", depends_on=["step-a"]),
        ])
        active = SpyActiveRunPointer(initial_run_id="run-params")
        metadata = RunMetadata(params={"key": "world"}, detected_env="")
        states = [_empty_run_state(), _empty_run_state(), _empty_run_state()]
        first_instance = _make_instance("step-a")
        interpolated_instance = StepInstance(
            step_id="step-b",
            instance_id="step-b-1",
            item=None,
            prompt="Hello world",
        )
        builder_spy = CapturingStepResultBuilder()

        sut, _, _, _ = self._make_sut(
            flow_def=flow,
            active_run=active,
            event_log_states=states,
            dag_sequences=[[first_instance], [interpolated_instance]],
            metadata=metadata,
            step_result_builder=builder_spy,
        )

        sut.flow_next()

        self.assertGreaterEqual(len(builder_spy.captured_instances), 1)
        self.assertEqual(builder_spy.captured_instances[0].prompt, "Hello world")


if __name__ == "__main__":
    unittest.main()
