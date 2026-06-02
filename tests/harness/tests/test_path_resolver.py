"""
solid-name: TestPathResolver
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for PathResolver. Verifies that references/ paths are correctly mapped
to the corresponding tests/ directory and that ValueError is raised when the resolved path does not
exist.
"""

import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE)

from path_resolver import PathResolver


class TestPathResolver(unittest.TestCase):
    def _assert_resolves(self, input_path: str, expected_suffix: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "tests" / Path(expected_suffix)
            target.mkdir(parents=True)
            resolver = PathResolver(root)
            result = resolver.resolve(input_path)
            self.assertEqual(result, target)

    def test_references_principles_srp_resolves_to_tests_principles_srp(self):
        self._assert_resolves("references/principles/SRP", "principles/SRP")

    def test_references_coding_apple_swiftui_resolves_to_tests_coding_apple_swiftui(self):
        self._assert_resolves("references/coding/apple/SwiftUI", "coding/apple/SwiftUI")

    def test_path_without_references_prefix_resolves_relative_to_tests(self):
        self._assert_resolves("principles/SRP", "principles/SRP")

    def test_raises_value_error_when_resolved_directory_does_not_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolver = PathResolver(root)
            with self.assertRaises(ValueError):
                resolver.resolve("references/principles/MISSING")


if __name__ == "__main__":
    unittest.main()
