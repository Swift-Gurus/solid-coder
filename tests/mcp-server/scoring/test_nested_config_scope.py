"""Verifies nested configuration directory scoping."""

import tempfile
import unittest
from pathlib import Path

from project_root_test_context import ProjectRootTestContext


_CONTEXT = ProjectRootTestContext(Path(__file__).resolve().parents[3] / "references")


"""
solid-name: NestedConfigScopeTests
solid-category: unit-test
solid-description: Verifies nested configuration applies only within its containing directory.
"""
class NestedConfigScopeTests(unittest.TestCase):
    def test_nested_config_applies_only_to_files_in_subdirectory(self):
        scorer = _CONTEXT.make_scorer()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            subdirectory = root / "src" / "tests"
            subdirectory.mkdir(parents=True)
            _CONTEXT.helper.write_at(root, {})
            _CONTEXT.helper.write_at(
                subdirectory,
                {"SRP": {"SRP-1": {"verb_count": {"disabled": True}}}},
            )

            inside = scorer.score_unit(
                {"verb_count": _CONTEXT.severe_value},
                "SRP-1",
                str(subdirectory / "FooTests.swift"),
            )
            outside = scorer.score_unit(
                {"verb_count": _CONTEXT.severe_value},
                "SRP-1",
                str(root / "src" / "Foo.swift"),
            )

            self.assertEqual(inside["final_severity"], "COMPLIANT")
            self.assertEqual(outside["final_severity"], "SEVERE")
