"""
solid-name: test_flow_harness_integration
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Integration test validating end-to-end workflow execution from initiation through completion with proper event logging and artifact creation.
"""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.active_run_locator import ActiveRunLocator
from harness.active_run_pointer_store import ActiveRunPointerStore
from harness.claude_agent_type_env_detector import ClaudeAgentTypeEnvDetector
from harness.execution_intent_resolver import ExecutionIntentResolver
from harness.flow_engine_assembly import build_default_assembly
from harness.flow_file_resolver import FlowFileResolver
from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_search_path_resolver import FlowSearchPathResolver
from harness.flow_starter import FlowStarter
from harness.flow_status_reader import FlowStatusReader
from harness.flow_stepper import FlowStepper
from harness.mcp_request_context_session_reader import McpRequestContextSessionReader
from harness.name_resolving_flow_loader import NameResolvingFlowLoader
from harness.output_recorder import OutputRecorder
from harness.path_checking import PathChecker
from harness.run_completion_checker import RunCompletionChecker
from harness.run_context_builder import RunContextBuilder
from harness.run_directory_scaffolder import RunDirectoryScaffolder
from harness.run_initializer import RunInitializer
from harness.run_metadata_store import RunMetadataStore
from harness.run_provisioner import RunProvisioner
from harness.run_snapshot_resolver import RunSnapshotResolver
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.startup_context_resolver import StartupContextResolver
from harness.step_output_validator import StepOutputValidator
from harness.step_result_builder import StepResultBuilder
from harness.turn_advancer import TurnAdvancer


_LINEAR_FLOW_YAML = textwrap.dedent("""    name: linear_3_step
    max_turns: 10
    steps:
      - id: step_one
        prompt: Do step one
      - id: step_two
        prompt: Do step two
        depends_on: [step_one]
      - id: step_three
        prompt: Do step three
        depends_on: [step_two]
""")


class TestFlowHarnessIntegration(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.runs_dir = Path(self._tmpdir) / "runs"
        self.runs_dir.mkdir(parents=True)

        self._flow_file = Path(self._tmpdir) / "linear_3_step.yaml"
        self._flow_file.write_text(_LINEAR_FLOW_YAML)

        assembly = build_default_assembly()
        active_run = ActiveRunPointerStore()
        base_dir_resolver = RunsBaseDirResolver(project_dir_fn=lambda: Path(self._tmpdir))
        metadata_store = RunMetadataStore()
        step_result_builder = StepResultBuilder(intent_resolver=ExecutionIntentResolver())
        run_locator = ActiveRunLocator(base_dir_resolver=base_dir_resolver, active_run=active_run)
        resolving_flow_loader = NameResolvingFlowLoader(
            file_resolver=FlowFileResolver(path_checker=PathChecker()),
            inner_loader=assembly.flow_loader,
        )
        run_snapshot_resolver = RunSnapshotResolver(
            event_replayer=assembly.event_replayer,
            context_builder=RunContextBuilder(),
            dag_runner=assembly.dag_runner,
        )

        starter = FlowStarter(
            startup_context=StartupContextResolver(
                env_detector=ClaudeAgentTypeEnvDetector(),
                base_dir_resolver=base_dir_resolver,
                search_paths=FlowSearchPathResolver(),
            ),
            flow_loader=resolving_flow_loader,
            run_provisioner=RunProvisioner(
                run_initializer=RunInitializer(active_run=active_run, scaffolder=RunDirectoryScaffolder()),
                metadata_store=metadata_store,
            ),
            event_appender=assembly.event_appender,
            run_snapshot_resolver=run_snapshot_resolver,
            step_result_builder=step_result_builder,
        )
        stepper = FlowStepper(
            run_locator=run_locator,
            metadata_store=metadata_store,
            flow_loader=resolving_flow_loader,
            run_snapshot_resolver=run_snapshot_resolver,
            output_validator=StepOutputValidator(schema_validator=assembly.schema_validator),
            session_reader=McpRequestContextSessionReader(),
            output_recorder=OutputRecorder(event_appender=assembly.event_appender),
            turn_advancer=TurnAdvancer(event_replayer=assembly.event_replayer, event_appender=assembly.event_appender),
            completion_checker=RunCompletionChecker(event_appender=assembly.event_appender, active_run=active_run),
            step_result_builder=step_result_builder,
        )
        status_reader = FlowStatusReader(
            run_locator=run_locator,
            flow_loader=resolving_flow_loader,
            run_snapshot_resolver=run_snapshot_resolver,
        )

        self.sut = FlowRunOrchestrator(starter=starter, stepper=stepper, status_reader=status_reader)

    def test_flow_start_to_done_completes_three_step_linear_flow(self):
        start_result = self.sut.flow_start(str(self._flow_file))

        self.assertTrue(len(start_result.steps) >= 1)
        run_id = start_result.run_id
        run_dir = self.runs_dir / run_id

        next1 = self.sut.flow_next()
        next2 = self.sut.flow_next()
        final = self.sut.flow_next()

        self.assertEqual(final.status, "done")

        active_json = self.runs_dir / "active.json"
        self.assertFalse(active_json.exists())

        self.assertTrue((run_dir / "workflow.yaml").exists())
        self.assertTrue((run_dir / "run-metadata.json").exists())

        events_path = run_dir / "events.jsonl"
        self.assertTrue(events_path.exists())
        lines = events_path.read_text().strip().splitlines()
        events = [json.loads(line) for line in lines]
        event_types = [e["event"] for e in events]

        self.assertIn("run_started", event_types)
        self.assertIn("run_completed", event_types)
        self.assertEqual(event_types.count("step_completed"), 3)
        self.assertEqual(event_types.count("session_step_recorded"), 3)
        self.assertEqual(event_types.count("turn_counted"), 3)


if __name__ == "__main__":
    unittest.main()
