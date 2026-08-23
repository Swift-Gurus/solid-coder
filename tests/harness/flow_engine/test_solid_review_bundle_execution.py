"""Tests the packaged review bundle through real flow orchestration."""

import tempfile
import textwrap
import unittest
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
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
        registrations = [
            *SourceOperationRegistrationsFactory(
                project_directory=lambda: self.run_root,
            ).make(),
            *ReviewOperationRegistrationsFactory().make(),
        ]
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.run_root
            ),
            plugin_root=_PROJECT_ROOT,
            operation_registrations=registrations,
        ).build()

    def test_buffer_reaches_every_applicable_file_and_unit_rule(self) -> None:
        started = self.sut.flow_start(
            "solid-review",
            params={
                "target": {
                    "kind": "buffer",
                    "path": str(self.target_path),
                    "content": self.source,
                }
            },
        )

        self.assertIsNone(started.error, started.error)
        self.assertTrue(started.steps)
        prompts = [step.prompt for step in started.steps]
        self.assertTrue(any("ProfileView" in prompt for prompt in prompts))
        self.assertTrue(any("ProfileStore" in prompt for prompt in prompts))
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
