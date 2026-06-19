"""
solid-name: TestModelProfileLoader
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Verifies correct resolution of named model profiles, appropriate error handling for unknown profiles, and fallback to project-level configuration when no model name is provided.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

_HOOKS_DIR = _PROJECT_ROOT / "hooks"
ensure_on_path(_HARNESS_DIR, _HERE, _HOOKS_DIR, _PROJECT_ROOT / "mcp-server" / "health" / "config")

from interfaces import TomlLoading  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402
from solid_coder_paths import CONFIG_DIR, CONFIG_LOCAL_TOML  # noqa: E402


class FakeTomlLoader(TomlLoading):
    def __init__(self, data_by_path: dict[str, dict] | None = None) -> None:
        self._data = data_by_path or {}

    def load_toml(self, path: Path) -> dict:
        return self._data.get(str(path), {})


class TestModelProfileLoader(unittest.TestCase):
    def test_named_profile_returns_model_profile_with_llm_data(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            models_dir = root / "tests" / "models"
            models_dir.mkdir(parents=True)
            qwen_toml = models_dir / "qwen.toml"
            qwen_toml.touch()
            loader = FakeTomlLoader({str(qwen_toml): {"llm": {"backend": "qwen"}, "inference": {}}})
            profile = ModelProfileLoader(root, loader).load("qwen")
            self.assertEqual(profile.output_dir_name, "qwen")
            self.assertEqual(profile.llm.get("backend"), "qwen")

    def test_missing_named_profile_raises(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "tests" / "models").mkdir(parents=True)
            loader = FakeTomlLoader()
            with self.assertRaises(RuntimeError):
                ModelProfileLoader(root, loader).load("unknown")

    def test_no_model_name_uses_project_toml_backend_as_output_dir(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            claude_dir = root / CONFIG_DIR
            claude_dir.mkdir()
            project_toml = claude_dir / CONFIG_LOCAL_TOML
            project_toml.touch()
            loader = FakeTomlLoader({
                str(project_toml): {"llm": {"backend": "claude"}, "inference": {}}
            })
            profile = ModelProfileLoader(root, loader).load(None)
            self.assertEqual(profile.output_dir_name, "claude")


if __name__ == "__main__":
    unittest.main()
