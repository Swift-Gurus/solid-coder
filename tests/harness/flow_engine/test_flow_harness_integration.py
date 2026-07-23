"""
solid-name: test_flow_harness_integration
solid-category: unit-test
solid-spec: [SPEC-013, SPEC-027]
solid-description: Integration test validating end-to-end workflow execution from initiation through completion with proper event logging and artifact creation, including file-sourced prompts, script steps, aliased includes, and attempts exhaustion.
"""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


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


class StubCommandAllowlistResolver:
    def __init__(self, executables: list[str]) -> None:
        self._executables = executables

    def resolve(self) -> list[str]:
        return self._executables


class FlowHarnessTestBuild(unittest.TestCase):
    """Base class assembling the full production wiring against a temp runs directory."""

    def _build(self, tmpdir: str, command_allowlist_resolver=None) -> FlowRunOrchestrator:
        base_dir_resolver = RunsBaseDirResolver(project_dir_fn=lambda: Path(tmpdir))
        return FlowRunOrchestratorFactory(
            base_dir_resolver=base_dir_resolver,
            command_allowlist_resolver=command_allowlist_resolver,
        ).build()


class TestFlowHarnessIntegration(FlowHarnessTestBuild):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.runs_dir = Path(self._tmpdir) / "runs"
        self.runs_dir.mkdir(parents=True)

        self._flow_file = Path(self._tmpdir) / "linear_3_step.yaml"
        self._flow_file.write_text(_LINEAR_FLOW_YAML)

        self.sut = self._build(self._tmpdir)

    def test_flow_start_to_done_completes_three_step_linear_flow(self):
        start_result = self.sut.flow_start(str(self._flow_file))

        self.assertTrue(len(start_result.steps) >= 1)
        run_id = start_result.run_id
        run_dir = self.runs_dir / run_id

        outputs = {s.instance_id: {} for s in start_result.steps}
        next1 = self.sut.flow_next(outputs)
        outputs = {s.instance_id: {} for s in next1.steps}
        next2 = self.sut.flow_next(outputs)
        outputs = {s.instance_id: {} for s in next2.steps}
        final = self.sut.flow_next(outputs)

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


class TestFlowHarnessScriptStepsAndIncludes(FlowHarnessTestBuild):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.runs_dir = Path(self._tmpdir) / "runs"
        self.runs_dir.mkdir(parents=True)

    def _write(self, name: str, content: str) -> Path:
        path = Path(self._tmpdir) / name
        path.write_text(textwrap.dedent(content))
        return path

    def _build_with_allowlist(self) -> FlowRunOrchestrator:
        return self._build(self._tmpdir, command_allowlist_resolver=StubCommandAllowlistResolver([sys.executable]))

    def _drive_to_done(self, sut, first_result, max_iterations: int = 5):
        result = first_result
        for _ in range(max_iterations):
            if result.status != "ready" or not result.steps:
                return result
            outputs = {step.instance_id: {} for step in result.steps if step.step_id in ("from_file", "sub.leaf")}
            if not outputs:
                return result
            result = sut.flow_next(outputs)
        return result

    def test_flow_combining_prompt_file_script_step_and_aliased_include_reaches_done(self):
        self._write("prompt.md", "Please review the change")
        succeed_script = Path(self._tmpdir) / "succeed.py"
        succeed_script.write_text('print(\'{"ok": true}\')\n')
        self._write("sub.yaml", """
            steps:
              - id: leaf
                prompt: Do the leaf step
        """)
        flow_file = self._write("combined.yaml", f"""
            name: combined
            max_turns: 10
            steps:
              - id: from_file
                prompt_file: prompt.md
              - id: gate
                type: script
                command: ["{sys.executable}", "{succeed_script}"]
                depends_on: [from_file]
              - include: sub.yaml
                as: sub
        """)

        sut = self._build_with_allowlist()
        start_result = sut.flow_start(str(flow_file))

        first_result = sut.flow_next({s.instance_id: {} for s in start_result.steps if s.step_id == "from_file"})
        result = self._drive_to_done(sut, first_result)

        self.assertEqual(result.status, "done")

    def test_script_step_exhausting_max_attempts_fails_the_run(self):
        fail_script = Path(self._tmpdir) / "fail.py"
        fail_script.write_text("import sys\nsys.exit(1)\n")
        flow_file = self._write("failing.yaml", f"""
            name: failing
            max_turns: 10
            steps:
              - id: gate
                type: script
                command: ["{sys.executable}", "{fail_script}"]
                max_attempts: 2
        """)

        sut = self._build_with_allowlist()
        start_result = sut.flow_start(str(flow_file))

        self.assertEqual(start_result.steps, [])
        self.assertIsNotNone(start_result.error)


if __name__ == "__main__":
    unittest.main()
