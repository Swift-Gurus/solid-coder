"""Verifies automatic project-root discovery for scoring configuration."""

import tempfile
import unittest
from pathlib import Path

from project_root_test_context import ProjectRootTestContext


_CONTEXT = ProjectRootTestContext(Path(__file__).resolve().parents[3] / "references")


"""
solid-name: ProjectRootAutoDetectionTests
solid-category: unit-test
solid-description: Verifies scoring discovers the project root from its configuration directory.
"""
class ProjectRootAutoDetectionTests(unittest.TestCase):
    def test_project_root_auto_detected_via_solid_coder_directory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "src" / "deep" / "Foo.swift"
            source.parent.mkdir(parents=True)
            _CONTEXT.helper.write_at(
                Path(temporary_directory),
                {"SRP": {"SRP-1": {"verb_count": {"disabled": True}}}},
            )

            result = _CONTEXT.make_scorer().score_unit(
                {"verb_count": _CONTEXT.severe_value},
                "SRP-1",
                str(source),
            )

            self.assertEqual(result["final_severity"], "COMPLIANT")
