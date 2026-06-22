"""
solid-description: Validates bare session timeout configuration and defaults.
solid-category: unit-test
"""

import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_config import bare_session_timeout  # noqa: E402


class TestBareSessionTimeout(unittest.TestCase):
    def test_default_is_300(self):
        with patch("hc_config_core.read_llm_section", return_value={}):
            self.assertEqual(bare_session_timeout(), 300)

    def test_reads_value_from_toml(self):
        with patch("hc_config_core.read_llm_section", return_value={"bare_session_timeout": 120}):
            self.assertEqual(bare_session_timeout(), 120)

    def test_falls_back_to_default_on_invalid_value(self):
        with patch("hc_config_core.read_llm_section", return_value={"bare_session_timeout": "not-a-number"}):
            self.assertEqual(bare_session_timeout(), 300)


if __name__ == "__main__":
    unittest.main()
