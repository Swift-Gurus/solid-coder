"""Tests the packaged review bundle through real flow orchestration."""

import tempfile
import textwrap
import unittest
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_TEST_HARNESS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))
sys.path.insert(0, str(_TEST_HARNESS_ROOT))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.project_context import ProjectDirectory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from bundled_review_rule_policy_writer import BundledReviewRulePolicyWriter
from review.review_operation_registrations_factory import (
    ReviewOperationRegistrationsFactory,
)
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)


"""
solid-name: TestSolidReviewBundleExecution
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-039, SPEC-041]
solid-description: Proves the packaged review bundle normalizes a buffer, fans out units, activates applicable rules, and supplies shared DRY context.
"""
class TestSolidReviewBundleExecution(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.target_path = self.run_root / "Profile.swift"
        self.source = textwrap.dedent(
            """
            import SwiftUI

            struct ProfileView: View {
                var body: some View { Text("Profile") }
            }

            actor ProfileStore {
                func load() async {}
            }
            """
        ).lstrip()
        project_directory = ProjectDirectory(path=self.run_root)
        registrations = [
            *SourceOperationRegistrationsFactory(
                project_directory=project_directory,
            ).make(),
            *ReviewOperationRegistrationsFactory().make(),
        ]
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.run_root
            ),
            plugin_root=_PROJECT_ROOT,
            project_directory=project_directory,
            operation_registrations=registrations,
        ).build()

    def test_prospective_text_selects_rules_without_entering_model_prompts(self) -> None:
        started = self._start_review({
            "kind": "text",
            "text": self.source,
            "virtual_path": str(self.target_path),
        })

        self.assertIsNone(started.error, started.error)
        self.assertTrue(started.steps)
        prompts = [step.prompt for step in started.steps]
        self.assertTrue(any("ProfileView" in prompt for prompt in prompts))
        self.assertTrue(any("ProfileStore" in prompt for prompt in prompts))
        self.assertFalse(any("var body: some View" in prompt for prompt in prompts))
        self.assertFalse(any("func load() async" in prompt for prompt in prompts))
        self.assertFalse(any("'code':" in prompt for prompt in prompts))
        self.assertFalse(any("'applicability':" in prompt for prompt in prompts))
        self.assertFalse(any("'tag_evidence':" in prompt for prompt in prompts))
        identities = [step.step_id for step in started.steps]
        self.assertTrue(any("code-smells" in identity for identity in identities))
        self.assertTrue(any("frontmatter" in identity for identity in identities))
        self.assertTrue(any("srp" in identity for identity in identities))
        self.assertTrue(any("dry" in identity for identity in identities))
        self.assertTrue(any("swiftui" in identity for identity in identities))
        self.assertTrue(
            any("structured-concurrency" in identity for identity in identities)
        )
        self.assertFalse(any("unit-testing" in identity for identity in identities))
        self.assertFalse(any("ui-testing" in identity for identity in identities))
        self.assertEqual(self._rule_step_count(identities, "code-smells"), 4)
        self.assertEqual(self._rule_step_count(identities, "frontmatter"), 6)
        self.assertEqual(self._rule_step_count(identities, "srp"), 2)
        self.assertEqual(self._rule_step_count(identities, "ocp"), 2)
        self.assertEqual(self._rule_step_count(identities, "lsp"), 2)
        self.assertEqual(self._rule_step_count(identities, "dry"), 2)
        self.assertEqual(self._rule_step_count(identities, "swiftui"), 11)
        self.assertEqual(
            self._rule_step_count(identities, "structured-concurrency"),
            14,
        )

    def test_file_review_applies_project_policy_before_rule_materialization(self) -> None:
        self.target_path.write_text(self.source, encoding="utf-8")
        BundledReviewRulePolicyWriter(
            plugin_root=_PROJECT_ROOT,
            project_root=self.run_root,
        ).write_only("srp")

        started = self._start_review({
            "kind": "file",
            "path": str(self.target_path),
        })

        self.assertIsNone(started.error, started.error)
        identities = [step.step_id for step in started.steps]
        rule_identities = [
            identity for identity in identities if ".rule_reviews." in identity
        ]
        self.assertTrue(rule_identities)
        self.assertTrue(all(".rule_reviews.srp-" in item for item in rule_identities))
        self.assertEqual(self._rule_step_count(rule_identities, "srp"), 2)
        prompts = [step.prompt for step in started.steps]
        self.assertTrue(any("ProfileView" in prompt for prompt in prompts))
        self.assertTrue(any("ProfileStore" in prompt for prompt in prompts))
        self.assertFalse(any("var body: some View" in prompt for prompt in prompts))
        self.assertFalse(any("func load() async" in prompt for prompt in prompts))
        self.assertFalse(any("'code':" in prompt for prompt in prompts))

    def test_aggregate_experiment_reuses_every_canonical_rule_step(self) -> None:
        self.target_path.write_text(self.source, encoding="utf-8")
        BundledReviewRulePolicyWriter(
            plugin_root=_PROJECT_ROOT,
            project_root=self.run_root,
        ).write_only("srp")

        started = self.sut.flow_start(
            "solid-file-review-aggregate",
            params={
                "target": {
                    "kind": "file",
                    "path": str(self.target_path),
                },
                "context_sources": [],
            },
        )

        self.assertIsNone(started.error, started.error)
        identities = [step.step_id for step in started.steps]
        self.assertEqual(self._rule_step_count(identities, "srp"), 8)
        self.assertTrue(all(step.batch is not None for step in started.steps))
        self.assertEqual(
            {step.batch.mode.value for step in started.steps},
            {"aggregate"},
        )

    def _start_review(self, target: dict):
        started = self.sut.flow_start("solid-review")
        self.assertIsNone(started.error, started.error)
        self.assertEqual(len(started.steps), 1)
        return self.sut.flow_next({
            started.steps[0].instance_id: {
                "target": target,
                "context_sources": [],
            }
        })

    @staticmethod
    def _rule_step_count(identities: list[str], rule_id: str) -> int:
        qualification = f".rule_reviews.{rule_id}-"
        return len([
            identity
            for identity in identities
            if qualification in identity
        ])


if __name__ == "__main__":
    unittest.main()
