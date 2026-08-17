"""
solid-name: test_review_rule_plan_preparer
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies project policy precedence is planned and persisted through production composition.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.project_policy_rule_decision import ProjectPolicyRuleDecision
from harness.review_rule_plan_preparer_factory import make_review_rule_plan_preparer


class TestReviewRulePlanPreparer(unittest.TestCase):

    def test_project_policy_precedes_workflow_default_and_is_snapshotted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project_root = root / "project"
            workflow_root = root / "plugin-workflows"
            run_dir = root / "run"
            policy_path = (
                project_root / ".solid-coder" / "policies" / "review.yaml"
            )
            workflow_path = workflow_root / "solid-srp-review" / "workflow.yaml"
            policy_path.parent.mkdir(parents=True)
            workflow_path.parent.mkdir(parents=True)
            run_dir.mkdir()
            policy_path.write_text(
                "version: 1\n"
                "rules:\n"
                "  - workflow_id: solid-srp-review\n"
                "    enabled: false\n"
                "    reason: Project-owned review policy.\n"
            )
            workflow_path.write_text(
                "id: solid-srp-review\n"
                "name: SRP Review\n"
                "max_turns: 3\n"
                "rule: {}\n"
                "steps:\n"
                "  - id: inspect\n"
                "    prompt: Inspect the supplied unit.\n"
            )

            plan = make_review_rule_plan_preparer(
                lambda: project_root
            ).prepare(run_dir, [workflow_root])

            decision = plan.rules[0].enablement
            self.assertIsInstance(decision, ProjectPolicyRuleDecision)
            self.assertFalse(decision.effective)
            self.assertEqual(decision.reason, "Project-owned review policy.")
            self.assertTrue((run_dir / "effective-rule-plan.json").is_file())
            self.assertEqual(
                (run_dir / "review-policy.yaml").read_text(),
                policy_path.read_text(),
            )


if __name__ == "__main__":
    unittest.main()
