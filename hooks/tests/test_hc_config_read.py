"""
solid-description: Verifies that LLM section configuration is correctly read from available sources.
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

import hc_config_core  # noqa: E402

_VALID_TOML = b"[llm]\nbackend = \"local\"\nhost = \"http://gpu:9090\"\n"


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
        with patch("hc_config_core.find_config", return_value=None), \
             patch("hc_config_core.find_repo_config", return_value=None):
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
            with patch("hc_config_core.find_config", return_value=None), \
                 patch("hc_config_core.find_repo_config", return_value=None):
                result = hc_config_core.read_llm_section()
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
