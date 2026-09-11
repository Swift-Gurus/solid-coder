"""Proves aggregate workflow execution feeds ordinary rule scoring."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.rule_review_result import RuleReviewResult
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: TestAggregateWorkflowRuleScoring
solid-category: integration-test
solid-spec: [SPEC-045]
solid-description: Proves multi-step aggregate rule outputs retain ordinary MCP scoring and audit behavior.
"""
class TestAggregateWorkflowRuleScoring(unittest.TestCase):
    def test_scores_original_metric_and_exception_steps(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project_root = Path(temporary.name)
        workflow = project_root / "workflow.yaml"
        workflow.write_text(
            textwrap.dedent(
                """
                id: aggregate-scored-rule
                name: Aggregate Scored Rule
                max_turns: 5
                execution:
                  mode: aggregate
                rule: {}
                steps:
                  - id: smell_count
                    type: metric
                    metric_id: TEST-1
                    prompt: Count the smell.
                    value: {type: integer, minimum: 0}
                    scoring:
                      severe: {operator: greater_than, value: 1}
                  - id: classify_exception
                    type: exception
                    prompt: Classify the exception.
                """
            ),
            encoding="utf-8",
        )
        orchestrator = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: project_root
            ),
            plugin_root=project_root,
        ).build()

        started = orchestrator.flow_start(str(workflow))
        audit = {
            "reasoning": "The inspected source supports this observation.",
            "evidence": "line 12",
        }
        completed = orchestrator.flow_next({
            "aggregate-scored-rule": {
                "aggregate-scored-rule": {
                    "smell_count": {
                        "value": 2,
                        "additional_info": audit,
                    },
                    "classify_exception": {
                        "is_exception": False,
                        "additional_info": audit,
                    },
                }
            }
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = RuleReviewResult.model_validate_json(
            (
                project_root
                / "runs"
                / started.run_id
                / "results"
                / "review"
                / "aggregate-scored-rule"
                / started.run_id
                / "result.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(result.scoring_authority, "mcp")
        self.assertEqual(result.severity, "SEVERE")
        self.assertEqual(result.metrics[0].metric_id, "TEST-1")
        self.assertEqual(result.metrics[0].value, 2)
        self.assertFalse(result.exception.is_exception)


if __name__ == "__main__":
    unittest.main()
