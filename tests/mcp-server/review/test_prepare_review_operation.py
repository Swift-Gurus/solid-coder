"""Tests deterministic normalization of review targets."""

import tempfile
import textwrap
import unittest
from pathlib import Path

from review.buffer_review_target import BufferReviewTarget
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory


"""
solid-name: TestPrepareReviewOperation
solid-category: unit-test
solid-spec: [SPEC-041]
solid-description: Proves prospective review buffers become typed files, units, applicability, evidence, and source context without stale disk reads.
"""
class TestPrepareReviewOperation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.target_path = self.project_root / "Profile.swift"
        self.target_path.write_text(
            "struct StaleDiskValue {}\n",
            encoding="utf-8",
        )
        self.prospective_source = textwrap.dedent(
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

    def test_buffer_content_drives_every_normalized_review_fact(self) -> None:
        result = PrepareReviewOperationFactory().make().execute(
            PrepareReviewInput(
                target=BufferReviewTarget(
                    path=self.target_path,
                    content=self.prospective_source,
                )
            )
        )

        review_file = result.review_file
        self.assertEqual(review_file.target.code, self.prospective_source)
        self.assertNotIn("StaleDiskValue", review_file.target.code)
        self.assertEqual(review_file.applicability.file_extension, ".swift")
        self.assertEqual(
            [unit.target.name for unit in result.units],
            ["ProfileView", "ProfileStore"],
        )
        self.assertTrue(
            all(unit.target.code in self.prospective_source for unit in result.units)
        )
        view = result.units[0]
        self.assertIn("swiftui", view.applicability.tags)
        self.assertIn("view", view.applicability.tags)
        self.assertTrue(view.tag_evidence)
        self.assertTrue(
            all(detection.evidence for detection in view.tag_evidence)
        )
        self.assertEqual(len(result.source_context.sources), 1)
        self.assertEqual(
            result.source_context.sources[0].content,
            self.prospective_source,
        )
        self.assertEqual(
            result.source_context.sources[0].path,
            self.target_path.resolve(),
        )


if __name__ == "__main__":
    unittest.main()
