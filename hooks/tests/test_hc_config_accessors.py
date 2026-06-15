"""
solid-description: Tests LLM configuration accessor defaults and config-driven overrides.
solid-category: unit-test
solid-spec: [SPEC-014]
"""

from pathlib import Path
from unittest.mock import patch
import unittest

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import hc_config  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
