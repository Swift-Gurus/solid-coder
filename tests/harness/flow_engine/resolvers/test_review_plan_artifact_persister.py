"""
solid-name: test_review_plan_artifact_persister
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies effective rule plans and authored project policies are durably snapshotted before execution.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.default_review_policy_audit import DefaultReviewPolicyAudit
from harness.default_review_policy_resolution import DefaultReviewPolicyResolution
from harness.effective_rule_plan import EffectiveRulePlan
from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.project_review_policy_resolution import ProjectReviewPolicyResolution
from harness.review_plan_artifact_persister import ReviewPlanArtifactPersister
from harness.review_policy import ReviewPolicy


class TestReviewPlanArtifactPersister(unittest.TestCase):

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_dir = Path(temporary.name)
        self.sut = ReviewPlanArtifactPersister()

    def test_persists_effective_plan_and_verbatim_project_policy(self):
        authored = "version: 1\nrules: []\n"
        source_path = Path("/project/.solid-coder/policies/review.yaml")
        resolution = ProjectReviewPolicyResolution(
            policy=ReviewPolicy(version=1),
            audit=ProjectReviewPolicyAudit(
                source_path=source_path,
                content_hash="policy-hash",
            ),
            authored_content=authored,
        )
        plan = EffectiveRulePlan(
            policy=ProjectReviewPolicyAudit(
                source_path=source_path,
                content_hash="policy-hash",
            ),
        )

        self.sut.persist(self.run_dir, plan, resolution)

        persisted_plan = json.loads(
            (self.run_dir / "effective-rule-plan.json").read_text()
        )
        self.assertEqual(persisted_plan["policy"]["source"], "project")
        self.assertEqual(persisted_plan["policy"]["content_hash"], "policy-hash")
        self.assertEqual(
            (self.run_dir / "review-policy.yaml").read_text(),
            authored,
        )

    def test_absent_project_policy_does_not_create_yaml_snapshot(self):
        resolution = DefaultReviewPolicyResolution()
        plan = EffectiveRulePlan(policy=DefaultReviewPolicyAudit())

        self.sut.persist(self.run_dir, plan, resolution)

        self.assertTrue((self.run_dir / "effective-rule-plan.json").is_file())
        self.assertFalse((self.run_dir / "review-policy.yaml").exists())


if __name__ == "__main__":
    unittest.main()
