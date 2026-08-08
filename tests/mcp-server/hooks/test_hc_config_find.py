"""
solid-description: Validates that local config discovery correctly identifies presence and absence without searching outside the project directory.
solid-category: unit-test
solid-spec: [SPEC-014]
"""

import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

import hc_config_core  # noqa: E402
from solid_coder_paths import CONFIG_DIR, CONFIG_LOCAL_TOML  # noqa: E402
from test_utils import write_toml  # noqa: E402


class TestFindConfig(unittest.TestCase):
    def _find(self, project_dir: Path):
        return hc_config_core.find_config(_cwd=project_dir)

    def test_returns_project_config_when_present(self):
        with tempfile.TemporaryDirectory() as d:
            write_toml(Path(d), b"[llm]\nbackend = \"local\"\n")
            result = self._find(Path(d))
            self.assertEqual(result, Path(d) / CONFIG_DIR / CONFIG_LOCAL_TOML)

    def test_returns_none_when_project_config_absent(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(self._find(Path(d)))

    def test_does_not_search_outside_project_dir(self):
        with tempfile.TemporaryDirectory() as project, \
             tempfile.TemporaryDirectory() as other:
            write_toml(Path(other), b"[llm]\nbackend = \"local\"\n")
            self.assertIsNone(self._find(Path(project)))


if __name__ == "__main__":
    unittest.main()
