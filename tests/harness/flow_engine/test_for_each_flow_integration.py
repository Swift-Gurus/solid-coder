"""Validates complete fan-out and fan-in behavior for ``for_each`` flow steps."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


_FLOW = """
    name: for_each_lifecycle
    max_turns: 20
    steps:
      - id: prepare
        prompt: Prepare review targets
        outputs:
          - name: files
            type: data
            schema:
              type: array
              items:
                type: string

      - id: review_file
        prompt: Review {{item}}
        depends_on: [prepare]
        for_each: "{{steps.prepare.outputs.files}}"
        max_attempts: 2
        outputs:
          - name: result
            type: data
            schema:
              type: string

      - id: summarize
        prompt: Summarize {{steps.review_file.outputs.result}}
        depends_on: [review_file]
"""


class _AllowlistResolver:
    def resolve(self) -> list[str]:
        return [sys.executable]


class TestForEachFlowIntegration(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.project_root = Path(temporary_directory.name)
        self.flow_path = self.project_root / "for_each.yaml"
        self.flow_path.write_text(textwrap.dedent(_FLOW), encoding="utf-8")
        self.sut = self._make_orchestrator()

    def _make_orchestrator(self) -> FlowRunOrchestrator:
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def test_yaml_collection_expands_to_one_ready_instance_per_item(self) -> None:
        result = self._start_fan_out(["Alpha.swift", "Beta.swift", "Gamma.swift"])

        self.assertEqual(
            [step.instance_id for step in result.steps],
            ["review_file-1", "review_file-2", "review_file-3"],
        )
        self.assertEqual(
            [step.prompt.splitlines()[0] for step in result.steps],
            [
                "Review Alpha.swift",
                "Review Beta.swift",
                "Review Gamma.swift",
            ],
        )

    def test_partial_submission_keeps_unfinished_instances_ready(self) -> None:
        expanded = self._start_fan_out(
            ["Alpha.swift", "Beta.swift", "Gamma.swift"]
        )

        result = self.sut.flow_next(
            {expanded.steps[0].instance_id: {"result": "Alpha result"}}
        )

        self.assertEqual(
            [step.instance_id for step in result.steps],
            ["review_file-2", "review_file-3"],
        )

    def test_replay_returns_only_instances_left_incomplete_before_interruption(self) -> None:
        expanded = self._start_fan_out(
            ["Alpha.swift", "Beta.swift", "Gamma.swift"]
        )
        self.sut.flow_next(
            {expanded.steps[0].instance_id: {"result": "Alpha result"}}
        )

        result = self._make_orchestrator().flow_next()

        self.assertEqual(
            [step.instance_id for step in result.steps],
            ["review_file-2", "review_file-3"],
        )

    def test_all_instance_outputs_are_aggregated_for_downstream_steps(self) -> None:
        expanded = self._start_fan_out(
            ["Alpha.swift", "Beta.swift", "Gamma.swift"]
        )

        result = self.sut.flow_next(
            {
                "review_file-1": {"result": "Alpha result"},
                "review_file-2": {"result": "Beta result"},
                "review_file-3": {"result": "Gamma result"},
            }
        )

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        self.assertIn("Alpha result", result.steps[0].prompt)
        self.assertIn("Beta result", result.steps[0].prompt)
        self.assertIn("Gamma result", result.steps[0].prompt)

    def test_empty_collection_completes_parent_and_releases_downstream_step(self) -> None:
        result = self._start_fan_out([])

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        self.assertEqual(result.steps[0].prompt, "Summarize []")

    def test_invalid_instance_retries_without_reopening_successful_instances(self) -> None:
        self._start_fan_out(["Alpha.swift", "Beta.swift", "Gamma.swift"])

        result = self.sut.flow_next(
            {
                "review_file-1": {"result": 1},
                "review_file-2": {"result": "Beta result"},
                "review_file-3": {"result": "Gamma result"},
            }
        )

        self.assertEqual(
            [step.instance_id for step in result.steps],
            ["review_file-1"],
        )
        self.assertIsNotNone(result.steps[0].rejection_reason)

    def test_invalid_siblings_do_not_share_an_attempt_budget(self) -> None:
        self._start_fan_out(["Alpha.swift", "Beta.swift", "Gamma.swift"])

        result = self.sut.flow_next(
            {
                "review_file-1": {"result": 1},
                "review_file-2": {"result": 2},
                "review_file-3": {"result": "Gamma result"},
            }
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(
            [step.instance_id for step in result.steps],
            ["review_file-1", "review_file-2"],
        )

    def test_script_for_each_executes_in_engine_and_aggregates_before_agent_step(self) -> None:
        script_path = self.project_root / "inspect.py"
        script_path.write_text(
            'print(\'{"result": "checked"}\')\n',
            encoding="utf-8",
        )
        process_flow = self.project_root / "process-for-each.yaml"
        process_flow.write_text(textwrap.dedent(f"""
            name: process_for_each
            max_turns: 20
            steps:
              - id: prepare
                prompt: Prepare targets
                outputs:
                  - name: files
                    type: data
                    schema:
                      type: array
                      items:
                        type: string

              - id: inspect
                type: script
                command: ["{sys.executable}", "{script_path}"]
                depends_on: [prepare]
                for_each: "{{{{steps.prepare.outputs.files}}}}"
                outputs:
                  - name: result
                    type: data
                    schema:
                      type: string

              - id: summarize
                prompt: Summarize {{{{steps.inspect.outputs.result}}}}
                depends_on: [inspect]
        """), encoding="utf-8")
        sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
            command_allowlist_resolver=_AllowlistResolver(),
        ).build()
        started = sut.flow_start(str(process_flow))

        result = sut.flow_next({
            started.steps[0].instance_id: {
                "files": ["Alpha.swift", "Beta.swift", "Gamma.swift"],
            }
        })

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        self.assertEqual(result.steps[0].prompt.count("checked"), 3)

    def _start_fan_out(self, files: list[str]):
        started = self.sut.flow_start(str(self.flow_path))
        self.assertEqual([step.step_id for step in started.steps], ["prepare"])
        return self.sut.flow_next(
            {started.steps[0].instance_id: {"files": files}}
        )


if __name__ == "__main__":
    unittest.main()
