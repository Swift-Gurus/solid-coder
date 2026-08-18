"""
solid-name: test_live_session_artifact_directory_creator
solid-category: test
solid-description: Verifies live-session evidence is stored under the backend-specific repository artifact convention.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from live_session_artifact_directory_creator import (  # noqa: E402
    LiveSessionArtifactDirectoryCreator,
)
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402


class TestLiveSessionArtifactDirectoryCreator(unittest.TestCase):

    def test_creates_unique_backend_specific_e2e_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project_root = Path(directory)
            scope = LiveSessionArtifactScope(domain="review", scenario="srp")

            first = LiveSessionArtifactDirectoryCreator().create(
                project_root,
                "codex",
                scope,
            )
            second = LiveSessionArtifactDirectoryCreator().create(
                project_root,
                "codex",
                scope,
            )

            expected_parent = (
                project_root
                / ".solid-coder"
                / ".artifacts"
                / "test"
                / "codex"
                / "e2e"
                / "review"
                / "srp"
            )
            self.assertEqual(first.parent, expected_parent)
            self.assertEqual(second.parent, expected_parent)
            self.assertNotEqual(first, second)
            self.assertTrue(first.is_dir())
            self.assertTrue(second.is_dir())

    def test_rejects_scope_that_is_not_two_safe_directory_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "single directory names"):
                LiveSessionArtifactDirectoryCreator().create(
                    Path(directory),
                    "codex",
                    LiveSessionArtifactScope(
                        domain="review",
                        scenario="../srp",
                    ),
                )


if __name__ == "__main__":
    unittest.main()
