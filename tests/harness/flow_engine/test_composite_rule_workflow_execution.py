"""
solid-name: TestCompositeRuleWorkflowExecution
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies an explicit all-rules include executes and finalizes independently owned metric and exception workflows.
"""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.review_result import ReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver


class TestCompositeRuleWorkflowExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.project_root = Path(temporary_directory.name)
        self.workflow_root = self.project_root / "workflows" / "review"
        self.workflow_path = self._write_workflows()
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()

    def test_finalizes_each_child_rule_and_publishes_one_ordered_review(self) -> None:
        started = self.sut.flow_start(
            str(self.workflow_path),
            params={
                "review_unit": {
                    "file_extension": ".swift",
                    "unit_kind": "class",
                    "tags": [],
                }
            },
        )

        self.assertEqual(len(started.steps), 4)
        completed = self.sut.flow_next({
            step.instance_id: self._output_for(step.step_id)
            for step in started.steps
        })

        self.assertEqual(completed.status, "done")
        run_directory = self.project_root / "runs" / started.run_id
        aggregate = ReviewResult.model_validate_json(
            (run_directory / "results" / "review" / "result.json").read_text()
        )
        self.assertEqual(aggregate.workflow_id, "composite-review")
        self.assertEqual(
            [result.workflow_id for result in aggregate.rule_results],
            ["a-rule", "z-rule"],
        )
        self.assertEqual(aggregate.severity, "SEVERE")
        for result in aggregate.rule_results:
            result_path = (
                run_directory
                / "results"
                / "review"
                / result.workflow_id
                / result.rule_instance_id
                / "result.json"
            )
            self.assertTrue(result_path.is_file())

        events = [
            json.loads(line)
            for line in (run_directory / "events.jsonl").read_text().splitlines()
        ]
        self.assertEqual(
            len([event for event in events if event["event"] == "rule_result_published"]),
            2,
        )

    def _write_workflows(self) -> Path:
        self._write_rule("z-rule", "Z-1")
        self._write_rule("a-rule", "A-1")
        parent = self.workflow_root / "composite"
        parent.mkdir(parents=True)
        path = parent / "workflow.yaml"
        path.write_text(
            textwrap.dedent(
                """
                id: composite-review
                name: Composite Review
                max_turns: 10
                steps:
                  - include:
                      rules: all
                    as: rule_reviews
                    with:
                      review_unit: "{{params.review_unit}}"
                """
            ),
            encoding="utf-8",
        )
        return path

    def _write_rule(self, workflow_id: str, metric_id: str) -> None:
        package = self.workflow_root / workflow_id
        package.mkdir(parents=True)
        (package / "workflow.yaml").write_text(
            textwrap.dedent(
                f"""
                id: {workflow_id}
                name: {workflow_id}
                max_turns: 5
                rule: {{}}
                steps:
                  - id: measure
                    type: metric
                    metric_id: {metric_id}
                    prompt: Measure the unit.
                    value: {{type: boolean}}
                    scoring:
                      severe: {{operator: equals, value: true}}
                  - id: classify_exception
                    type: exception
                    prompt: Classify the exception.
                """
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _output_for(step_id: str) -> dict:
        additional_info = {
            "reasoning": "The source supports this observation.",
            "evidence": "line 4",
        }
        if step_id.endswith("measure"):
            return {
                "value": step_id.startswith("rule_reviews.z-rule"),
                "additional_info": additional_info,
            }
        return {
            "is_exception": False,
            "additional_info": additional_info,
        }


if __name__ == "__main__":
    unittest.main()
