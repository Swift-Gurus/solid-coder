"""Tests project scoring policy during collection-backed metric execution."""

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.project_context import ProjectDirectory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: TestEffectiveCollectionMetricPolicyExecution
solid-category: integration-test
solid-spec: [SPEC-053, SPEC-054]
solid-description: Verifies project scoring overrides reach executable collection-backed metrics.
"""
class TestEffectiveCollectionMetricPolicyExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow_path = self.project_root / "workflow.yaml"
        self.workflow_path.write_text(
            textwrap.dedent(
                """
                id: detached-task-review
                name: Detached Task Review
                max_turns: 5
                rule: {}
                steps:
                  - id: analyze_task_sites
                    prompt: Classify every task site.
                    outputs:
                      - name: task_sites
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            additionalProperties: false
                            required: [classification]
                            properties:
                              classification: {type: string}
                  - id: detached_task_count
                    type: metric
                    metric_id: DT-1
                    depends_on: [analyze_task_sites]
                    value: {type: integer, minimum: 0}
                    scoring:
                      source: "{{steps.analyze_task_sites.outputs.task_sites}}"
                      when:
                        ref: "{{item.classification}}"
                        equals: DETACHED
                      severe: {operator: greater_than_or_equal, value: 1}
                  - id: classify_exception
                    type: exception
                    depends_on: [detached_task_count]
                    prompt: Classify the whole-rule exception.
                """
            ),
            encoding="utf-8",
        )
        policy_directory = self.project_root / ".solid-coder" / "policies"
        policy_directory.mkdir(parents=True)
        (policy_directory / "review.yaml").write_text(
            textwrap.dedent(
                """
                version: 1
                rules:
                  - workflow_id: detached-task-review
                    metrics:
                      - id: DT-1
                        scoring:
                          severe:
                            operator: greater_than_or_equal
                            value: 3
                        reason: Permit two detached sites in this project.
                  - workflow_id: depth-review
                    metrics:
                      - id: DEPTH-1
                        scoring:
                          severe:
                            operator: greater_than_or_equal
                            value: 10
                        reason: Permit nesting depths below ten in this project.
                """
            ),
            encoding="utf-8",
        )
        self.engine = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
            project_directory=ProjectDirectory(path=self.project_root),
        ).build()

    def test_project_scoring_override_replaces_authored_collection_metric_band(
        self,
    ) -> None:
        started = self.engine.flow_start(str(self.workflow_path))
        exception = self.engine.flow_next({
            started.steps[0].instance_id: {
                "task_sites": [
                    {"classification": "DETACHED"},
                    {"classification": "DETACHED"},
                ]
            }
        })
        completed = self.engine.flow_next({
            exception.steps[0].instance_id: {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "No whole-rule exception applies.",
                    "evidence": "The unit performs runtime behavior.",
                },
            }
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._result(started.run_id)
        self.assertEqual(result["metrics"][0]["value"], 2)
        self.assertEqual(result["metrics"][0]["severity"], "COMPLIANT")
        self.assertNotIn("matching_band", result["metrics"][0])

    def test_project_scoring_override_applies_to_reducer_value(self) -> None:
        workflow_path = self.project_root / "depth.yaml"
        workflow_path.write_text(
            textwrap.dedent(self._depth_workflow()),
            encoding="utf-8",
        )
        started = self.engine.flow_start(str(workflow_path))
        exception = self.engine.flow_next({
            started.steps[0].instance_id: {
                "views": [{"depth": 2}, {"depth": 5}, {"depth": 3}]
            }
        })
        completed = self.engine.flow_next({
            exception.steps[0].instance_id: {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "No whole-rule exception applies.",
                    "evidence": "The reviewed unit contains runtime behavior.",
                },
            }
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._result(started.run_id, "depth-review")
        self.assertEqual(result["metrics"][0]["value"], 5)
        self.assertEqual(result["metrics"][0]["severity"], "COMPLIANT")
        self.assertNotIn("matching_band", result["metrics"][0])

    def _result(
        self,
        run_id: str,
        workflow_id: str = "detached-task-review",
    ) -> dict:
        result_path = (
            self.project_root
            / "runs"
            / run_id
            / "results"
            / "review"
            / workflow_id
            / run_id
            / "result.json"
        )
        return json.loads(result_path.read_text(encoding="utf-8"))

    def _depth_workflow(self) -> str:
        return """
        id: depth-review
        name: Depth Review
        max_turns: 5
        rule: {}
        steps:
          - id: analyze_views
            prompt: Measure view depths.
            outputs:
              - name: views
                type: data
                schema:
                  type: array
                  items:
                    type: object
                    additionalProperties: false
                    required: [depth]
                    properties:
                      depth: {type: integer}
          - id: maximum_depth
            type: metric
            metric_id: DEPTH-1
            depends_on: [analyze_views]
            value: {type: integer, minimum: 0}
            scoring:
              source: "{{steps.analyze_views.outputs.views}}"
              reducer:
                type: maximum
                value: "{{item.depth}}"
              severe: {operator: greater_than_or_equal, value: 5}
          - id: classify_exception
            type: exception
            depends_on: [maximum_depth]
            prompt: Classify the whole-rule exception.
        """


if __name__ == "__main__":
    unittest.main()
