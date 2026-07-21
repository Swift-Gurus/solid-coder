"""
solid-name: test_flow_file_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests resolving a flow name to a concrete YAML path across search directories, with literal-path fallback.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_file_resolver import FlowFileResolver


class TestFlowFileResolver(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.project_dir = Path(self._tmpdir) / "project"
        self.plugin_dir = Path(self._tmpdir) / "plugin"
        self.project_dir.mkdir(parents=True)
        self.plugin_dir.mkdir(parents=True)
        self.sut = FlowFileResolver(path_checker=_RealPathChecker())

    def test_resolves_bare_name_to_yaml_in_first_search_dir(self):
        flow_file = self.project_dir / "code_review.yaml"
        flow_file.write_text("name: code_review\nsteps: []\n")

        result = self.sut.resolve("code_review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, str(flow_file))

    def test_resolves_bare_name_to_yml_extension(self):
        flow_file = self.project_dir / "code_review.yml"
        flow_file.write_text("name: code_review\nsteps: []\n")

        result = self.sut.resolve("code_review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, str(flow_file))

    def test_project_search_dir_takes_precedence_over_later_dirs(self):
        project_file = self.project_dir / "code_review.yaml"
        project_file.write_text("name: code_review\nsteps: []\n")
        plugin_file = self.plugin_dir / "code_review.yaml"
        plugin_file.write_text("name: code_review\nsteps: []\n")

        result = self.sut.resolve("code_review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, str(project_file))

    def test_falls_back_to_second_search_dir_when_first_has_no_match(self):
        plugin_file = self.plugin_dir / "code_review.yaml"
        plugin_file.write_text("name: code_review\nsteps: []\n")

        result = self.sut.resolve("code_review", [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, str(plugin_file))

    def test_returns_literal_flow_unchanged_when_no_search_dir_matches(self):
        literal_path = str(Path(self._tmpdir) / "somewhere" / "custom.yaml")

        result = self.sut.resolve(literal_path, [str(self.project_dir), str(self.plugin_dir)])

        self.assertEqual(result, literal_path)

    def test_returns_literal_flow_unchanged_when_no_search_paths_given(self):
        result = self.sut.resolve("code_review", [])

        self.assertEqual(result, "code_review")


class _RealPathChecker:
    def exists(self, path: str) -> bool:
        return Path(path).exists()


if __name__ == "__main__":
    unittest.main()
