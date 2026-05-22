"""
solid-description: Unit tests verifying that the LLM configuration module resolves settings with correct source precedence.
solid-category: unit-test
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import hc_config

_INVALID_TOML = "not valid toml"
_VALID_TOML = b"[llm]\nbackend = \"local\"\nhost = \"http://gpu:9090\"\n"


class TestResolve(unittest.TestCase):
    def test_env_var_takes_precedence_over_config(self):
        with patch("hc_config._read_config_file", return_value={"backend": "local"}), \
             patch.dict(os.environ, {"SOLID_CODER_LLM_BACKEND": "claude"}):
            self.assertEqual(hc_config.llm_backend(), "claude")

    def test_config_file_used_when_env_absent(self):
        with patch("hc_config._read_config_file", return_value={"backend": "local"}), \
             patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SOLID_CODER_LLM_BACKEND", None)
            self.assertEqual(hc_config.llm_backend(), "local")

    def test_default_used_when_both_absent(self):
        with patch("hc_config._read_config_file", return_value={}), \
             patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SOLID_CODER_LLM_BACKEND", None)
            self.assertEqual(hc_config.llm_backend(), "claude")

    def test_default_host_is_localhost_8080(self):
        with patch("hc_config._read_config_file", return_value={}), \
             patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SOLID_CODER_LLM_HOST", None)
            self.assertEqual(hc_config.llm_host(), "http://localhost:8080")

    def test_default_model_is_local(self):
        with patch("hc_config._read_config_file", return_value={}), \
             patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SOLID_CODER_LLM_MODEL", None)
            self.assertEqual(hc_config.llm_model(), "local")


class TestReadConfigFile(unittest.TestCase):
    def test_returns_empty_when_file_missing(self):
        with patch("hc_config._CONFIG_PATH", Path("/nonexistent/path.toml")):
            self.assertEqual(hc_config._read_config_file(), {})

    def test_returns_empty_dict_on_invalid_toml(self):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False, mode="w") as f:
            f.write(_INVALID_TOML)
            tmp = Path(f.name)
        try:
            with patch("hc_config._CONFIG_PATH", tmp):
                result = hc_config._read_config_file()
            self.assertIsInstance(result, dict)
        finally:
            tmp.unlink()

    def test_reads_llm_section_when_tomllib_available(self):
        try:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            self.skipTest("No TOML parser available")

        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(_VALID_TOML)
            tmp = Path(f.name)
        try:
            with patch("hc_config._CONFIG_PATH", tmp):
                result = hc_config._read_config_file()
            self.assertEqual(result.get("backend"), "local")
            self.assertEqual(result.get("host"), "http://gpu:9090")
        finally:
            tmp.unlink()


if __name__ == "__main__":
    unittest.main()
