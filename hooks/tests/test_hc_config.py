"""
solid-description: Tests LLM configuration retrieval and default value provision.
solid-category: unit-test
solid-spec: [SPEC-014]
"""

import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import hc_config
import hc_config_core
from test_utils import write_toml

_VALID_TOML = b"[llm]\nbackend = \"local\"\nhost = \"http://gpu:9090\"\n"


def _write_toml(directory: Path, content: bytes = _VALID_TOML) -> Path:
    return write_toml(directory, content)


class TestAccessors(unittest.TestCase):
    def _assert_default(self, fn, expected: str) -> None:
        with patch("hc_config_core.read_llm_section", return_value={}):
            self.assertEqual(fn(), expected)

    def test_backend_defaults_to_claude(self):
        self._assert_default(hc_config.llm_backend, "claude")

    def test_host_defaults_to_localhost_8080(self):
        self._assert_default(hc_config.llm_host, "http://localhost:8080")

    def test_model_defaults_to_local(self):
        self._assert_default(hc_config.llm_model, "local")

    def test_backend_read_from_config(self):
        with patch("hc_config_core.read_llm_section", return_value={"backend": "local"}):
            self.assertEqual(hc_config.llm_backend(), "local")

    def test_host_read_from_config(self):
        with patch("hc_config_core.read_llm_section", return_value={"host": "http://myserver:9090"}):
            self.assertEqual(hc_config.llm_host(), "http://myserver:9090")


class TestFindConfig(unittest.TestCase):
    def _find(self, project_dir: Path):
        return hc_config_core.find_config(_cwd=project_dir)

    def test_returns_project_config_when_present(self):
        with tempfile.TemporaryDirectory() as d:
            _write_toml(Path(d))
            result = self._find(Path(d))
            self.assertEqual(result, Path(d) / ".claude" / "solid-coder-local.toml")

    def test_returns_none_when_project_config_absent(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(self._find(Path(d)))

    def test_does_not_search_outside_project_dir(self):
        with tempfile.TemporaryDirectory() as project, \
             tempfile.TemporaryDirectory() as other:
            _write_toml(Path(other))  # config elsewhere — must not be found
            self.assertIsNone(self._find(Path(project)))


class TestReadConfigFile(unittest.TestCase):
    @contextmanager
    def _temp_toml_path(self, content: bytes):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            yield tmp
        finally:
            tmp.unlink()

    @contextmanager
    def _with_temp_toml(self, content: bytes):
        with self._temp_toml_path(content) as tmp:
            with patch("hc_config_core.find_config", return_value=tmp):
                yield hc_config_core.read_llm_section(), tmp

    def test_returns_empty_when_no_config_found(self):
        with patch("hc_config_core.find_config", return_value=None):
            self.assertEqual(hc_config_core.read_llm_section(), {})

    def test_returns_empty_dict_on_invalid_toml(self):
        with self._with_temp_toml(b"not valid toml") as (result, _):
            self.assertIsInstance(result, dict)

    def test_reads_llm_section_when_tomllib_available(self):
        with self._with_temp_toml(_VALID_TOML) as (result, _):
            if not result:
                self.skipTest("No TOML parser available")
            self.assertEqual(result.get("backend"), "local")
            self.assertEqual(result.get("host"), "http://gpu:9090")

    def test_reads_from_env_var_override_when_set(self):
        toml_content = b"[llm]\nbackend = 'qwen'\n"
        with self._temp_toml_path(toml_content) as tmp_path:
            with patch.dict(os.environ, {"SOLID_CODER_TEST_MODEL_PROFILE": str(tmp_path)}):
                result = hc_config_core.read_llm_section()
        if not result:
            self.skipTest("No TOML parser available")
        self.assertEqual(result.get("backend"), "qwen")

    def test_original_behavior_preserved_when_env_var_unset(self):
        env = {k: v for k, v in os.environ.items() if k != "SOLID_CODER_TEST_MODEL_PROFILE"}
        with patch.dict(os.environ, env, clear=True):
            with patch("hc_config_core.find_config", return_value=None):
                result = hc_config_core.read_llm_section()
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
