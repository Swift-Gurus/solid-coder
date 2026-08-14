"""Verifies explicit project-root configuration discovery."""

import tempfile
import unittest
from pathlib import Path

from project_root_test_context import ProjectRootTestContext


_CONTEXT = ProjectRootTestContext(Path(__file__).resolve().parents[3] / "references")


"""
solid-name: ExplicitProjectRootTests
solid-category: unit-test
solid-description: Verifies scoring uses an explicitly supplied project root for configuration discovery.
"""
class ExplicitProjectRootTests(unittest.TestCase):
    def test_config_at_project_root_found_when_project_root_passed(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "src" / "deep" / "Foo.swift"
            source.parent.mkdir(parents=True)
            _CONTEXT.helper.write_at(
                Path(temporary_directory),
                {"SRP": {"SRP-1": {"verb_count": {"disabled": True}}}},
            )

            result = _CONTEXT.make_scorer(temporary_directory).score_unit(
                {"verb_count": _CONTEXT.severe_value},
                "SRP-1",
                str(source),
            )

            self.assertEqual(result["final_severity"], "COMPLIANT")
