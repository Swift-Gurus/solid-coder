"""
solid-name: test_effective_rule_plan_builder
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies project policy overrides workflow defaults in a deterministic auditable rule plan.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.effective_rule_plan_builder import EffectiveRulePlanBuilder
from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.project_policy_rule_decision import ProjectPolicyRuleDecision
from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.project_review_policy_resolution import ProjectReviewPolicyResolution
from harness.review_policy import ReviewPolicy
from harness.review_policy_metric_override import ReviewPolicyMetricOverride
from harness.review_policy_rule_override import ReviewPolicyRuleOverride
from harness.rule_declaration import RuleDeclaration
from harness.rule_enablement_resolver import RuleEnablementResolver
from harness.rule_plan_entry_builder import RulePlanEntryBuilder
from harness.rule_workflow_origin import RuleWorkflowOrigin
from harness.rule_workflow_origin_resolver import RuleWorkflowOriginResolver
from harness.sha256_content_hasher import Sha256ContentHasher
from harness.workflow_catalog import WorkflowCatalog
from harness.workflow_default_rule_decision import WorkflowDefaultRuleDecision
from harness.workflow_source import WorkflowSource
from harness.review_policy_target_validator import ReviewPolicyTargetValidator


class TestEffectiveRulePlanBuilder(unittest.TestCase):

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name) / "project"
        self.plugin_root = Path(temporary.name) / "plugin"
        self.project_root.mkdir()
        self.plugin_root.mkdir()
        error_factory = FlowValidationErrorFactory()
        self.sut = EffectiveRulePlanBuilder(
            target_validator=ReviewPolicyTargetValidator(error_factory),
            entry_builder=RulePlanEntryBuilder(
                content_hasher=Sha256ContentHasher(),
                enablement_resolver=RuleEnablementResolver(),
                origin_resolver=RuleWorkflowOriginResolver(
                    lambda: self.project_root
                ),
                error_factory=error_factory,
            ),
        )

    def test_project_policy_enablement_takes_precedence_over_workflow_default(self):
        source = self._source(
            root=self.plugin_root,
            workflow_id="solid-srp-review",
            content="id: solid-srp-review\nrule: {}\n",
        )
        policy_content = "version: 1\nrules:\n  - workflow_id: solid-srp-review\n    enabled: false\n"
        resolution = ProjectReviewPolicyResolution(
            policy=ReviewPolicy(
                version=1,
                rules=[
                    ReviewPolicyRuleOverride(
                        workflow_id="solid-srp-review",
                        enabled=False,
                        reason="The project uses another responsibility check.",
                    )
                ],
            ),
            audit=ProjectReviewPolicyAudit(
                source_path=(self.project_root / ".solid-coder/policies/review.yaml"),
                content_hash=hashlib.sha256(
                    policy_content.encode("utf-8")
                ).hexdigest(),
            ),
            authored_content=policy_content,
        )

        plan = self.sut.build(WorkflowCatalog([source]), resolution)

        entry = plan.rules[0]
        self.assertIsInstance(entry.enablement, ProjectPolicyRuleDecision)
        self.assertTrue(entry.enablement.authored_default)
        self.assertFalse(entry.enablement.client_requested)
        self.assertFalse(entry.enablement.effective)
        self.assertEqual(
            entry.enablement.policy.content_hash,
            resolution.audit.content_hash,
        )
        self.assertEqual(
            entry.enablement.reason,
            "The project uses another responsibility check.",
        )

    def test_rules_without_project_override_retain_the_workflow_default(self):
        source = self._source(
            root=self.plugin_root,
            workflow_id="solid-ocp-review",
            content="id: solid-ocp-review\nrule: {}\n",
        )
        resolution = ProjectReviewPolicyResolution(
            policy=ReviewPolicy(version=1),
            audit=ProjectReviewPolicyAudit(
                source_path=(self.project_root / ".solid-coder/policies/review.yaml"),
                content_hash="policy-hash",
            ),
            authored_content="version: 1\n",
        )

        plan = self.sut.build(WorkflowCatalog([source]), resolution)

        self.assertIsInstance(plan.rules[0].enablement, WorkflowDefaultRuleDecision)
        self.assertTrue(plan.rules[0].enablement.effective)

    def test_records_stable_origin_source_and_workflow_hashes(self):
        project_source = self._source(
            root=self.project_root / ".solid-coder" / "workflows",
            workflow_id="acme-accessibility",
            content="id: acme-accessibility\nrule:\n  tags: [swiftui]\n",
        )
        plugin_source = self._source(
            root=self.plugin_root,
            workflow_id="solid-srp-review",
            content="id: solid-srp-review\nrule: {}\n",
        )

        plan = self.sut.build(
            WorkflowCatalog([plugin_source, project_source]),
            ProjectReviewPolicyResolution(
                policy=ReviewPolicy(version=1),
                audit=ProjectReviewPolicyAudit(
                    source_path=(self.project_root / ".solid-coder/policies/review.yaml"),
                    content_hash="policy-hash",
                ),
                authored_content="version: 1\n",
            ),
        )

        self.assertEqual(
            [entry.workflow_id for entry in plan.rules],
            ["acme-accessibility", "solid-srp-review"],
        )
        client, bundled = plan.rules
        self.assertEqual(client.origin, RuleWorkflowOrigin.PROJECT)
        self.assertEqual(bundled.origin, RuleWorkflowOrigin.PLUGIN)
        self.assertEqual(client.source_path, project_source.entry_path.resolve())
        self.assertEqual(
            client.workflow_hash,
            hashlib.sha256(project_source.entry_path.read_bytes()).hexdigest(),
        )

    def test_rejects_policy_records_for_unknown_workflows(self):
        resolution = ProjectReviewPolicyResolution(
            policy=ReviewPolicy(
                version=1,
                rules=[ReviewPolicyRuleOverride(workflow_id="missing-rule")],
            ),
            audit=ProjectReviewPolicyAudit(
                source_path=(self.project_root / ".solid-coder/policies/review.yaml"),
                content_hash="policy-hash",
            ),
            authored_content="version: 1\n",
        )

        with self.assertRaisesRegex(FlowValidationError, "missing-rule"):
            self.sut.build(WorkflowCatalog([]), resolution)

    def test_rejects_metric_override_for_rule_without_scoring_contract(self):
        source = self._source(
            root=self.plugin_root,
            workflow_id="solid-srp-review",
            content="id: solid-srp-review\nrule: {}\n",
        )
        resolution = ProjectReviewPolicyResolution(
            policy=ReviewPolicy(
                version=1,
                rules=[
                    ReviewPolicyRuleOverride(
                        workflow_id="solid-srp-review",
                        metrics=[ReviewPolicyMetricOverride(id="SRP-1")],
                    )
                ],
            ),
            audit=ProjectReviewPolicyAudit(
                source_path=(self.project_root / ".solid-coder/policies/review.yaml"),
                content_hash="policy-hash",
            ),
            authored_content="version: 1\n",
        )

        with self.assertRaisesRegex(FlowValidationError, "does not declare engine scoring"):
            self.sut.build(WorkflowCatalog([source]), resolution)

    def _source(self, root: Path, workflow_id: str, content: str) -> WorkflowSource:
        package_root = root / workflow_id
        package_root.mkdir(parents=True)
        entry_path = package_root / "workflow.yaml"
        entry_path.write_text(content)
        return WorkflowSource(
            id=workflow_id,
            entry_path=entry_path,
            package_root=package_root,
            rule=RuleDeclaration(),
        )


if __name__ == "__main__":
    unittest.main()
