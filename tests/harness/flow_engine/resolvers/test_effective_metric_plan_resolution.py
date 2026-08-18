"""
solid-name: TestEffectiveMetricPlanResolution
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies workflow metric defaults and project scoring overrides resolve into one auditable effective plan.
"""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.review_rule_plan_preparer_factory import make_review_rule_plan_preparer


class TestEffectiveMetricPlanResolution(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.root = Path(temporary_directory.name)
        self.project_root = self.root / "project"
        self.workflow_root = self.root / "plugin-workflows"
        self.run_directory = self.root / "run"
        self.project_root.mkdir()
        self.run_directory.mkdir()
        package = self.workflow_root / "solid-srp-review"
        package.mkdir(parents=True)
        (package / "workflow.yaml").write_text(
            textwrap.dedent(
                """
                id: solid-srp-review
                name: Single Responsibility Review
                max_turns: 10
                rule:
                  category: solid
                steps:
                  - id: verb_count
                    type: metric
                    metric_id: SRP-1
                    prompt: Count responsibility verbs.
                    value: {type: integer, minimum: 0}
                    scoring:
                      minor: {operator: greater_than_or_equal, value: 3}
                      severe: {operator: greater_than, value: 5}
                  - id: classify_exception
                    type: exception
                    prompt: Classify an SRP exception.
                """
            )
        )

    def test_preserves_workflow_metric_defaults_without_project_policy(self) -> None:
        plan = self._prepare()

        metric = plan.rules[0].metrics[0]
        self.assertEqual(metric.metric_id, "SRP-1")
        self.assertTrue(metric.effective_enabled)
        self.assertEqual(metric.authored_scoring.minor.value, 3)
        self.assertEqual(metric.effective_scoring.severe.value, 5)
        self.assertIsNone(metric.policy_override)

    def test_project_metric_scoring_replaces_workflow_bands_atomically(self) -> None:
        self._write_policy(
            """
            version: 1
            rules:
              - workflow_id: solid-srp-review
                metrics:
                  - id: SRP-1
                    scoring:
                      minor: {operator: greater_than_or_equal, value: 4}
                      severe: {operator: greater_than, value: 8}
                    reason: Larger orchestration units are accepted here.
            """
        )

        plan = self._prepare()

        metric = plan.rules[0].metrics[0]
        self.assertEqual(metric.authored_scoring.severe.value, 5)
        self.assertEqual(metric.effective_scoring.severe.value, 8)
        self.assertEqual(metric.policy_override.requested_scoring.severe.value, 8)
        self.assertEqual(
            metric.policy_override.reason,
            "Larger orchestration units are accepted here.",
        )

    def test_rejects_project_override_for_unknown_metric(self) -> None:
        self._write_policy(
            """
            version: 1
            rules:
              - workflow_id: solid-srp-review
                metrics:
                  - id: SRP-404
                    enabled: false
            """
        )

        with self.assertRaisesRegex(FlowValidationError, "SRP-404"):
            self._prepare()

    def _prepare(self):
        return make_review_rule_plan_preparer(
            project_directory=lambda: self.project_root
        ).prepare(
            run_dir=self.run_directory,
            workflow_roots=[self.workflow_root],
        )

    def _write_policy(self, source: str) -> None:
        policy_directory = self.project_root / ".solid-coder" / "policies"
        policy_directory.mkdir(parents=True)
        (policy_directory / "review.yaml").write_text(textwrap.dedent(source))


if __name__ == "__main__":
    unittest.main()
