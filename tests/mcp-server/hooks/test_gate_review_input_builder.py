"""Tests prospective gate input construction."""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from gate_review_input_builder import GateReviewInputBuilder  # noqa: E402
from patch_file_simulation import PatchFileSimulation  # noqa: E402
from patch_review_context import PatchReviewContext  # noqa: E402


"""
solid-name: TestGateReviewInputBuilder
solid-category: unit-test
solid-spec: [SPEC-036, SPEC-041]
solid-description: Proves prospective source requests become text-backed review inputs with shared patch context.
"""
class TestGateReviewInputBuilder(unittest.TestCase):
    def test_builds_text_target_for_nonexistent_destination(self) -> None:
        result = GateReviewInputBuilder().build(
            "struct NewFeature {}",
            "/project/Sources/NewFeature.swift",
            None,
        )

        self.assertEqual(result.target.kind, "text")
        self.assertEqual(result.target.text, "struct NewFeature {}")
        self.assertEqual(
            result.target.virtual_path,
            "/project/Sources/NewFeature.swift",
        )
        self.assertEqual(result.context_sources, [])

    def test_preserves_other_prospective_patch_files_as_context(self) -> None:
        result = GateReviewInputBuilder().build(
            "struct First {}",
            "/project/Sources/First.swift",
            PatchReviewContext(proposed_files=[
                PatchFileSimulation(
                    file_path="/project/Sources/First.swift",
                    content="struct First {}",
                    existing_content="",
                    low_risk=False,
                ),
                PatchFileSimulation(
                    file_path="/project/Sources/Second.swift",
                    content="struct Second {}",
                    existing_content="",
                    low_risk=False,
                ),
            ]),
        )

        self.assertEqual(len(result.context_sources), 1)
        sibling = result.context_sources[0]
        self.assertEqual(sibling.kind, "text")
        self.assertEqual(sibling.text, "struct Second {}")
        self.assertEqual(
            sibling.virtual_path,
            "/project/Sources/Second.swift",
        )


if __name__ == "__main__":
    unittest.main()
