"""
solid-description: Verifies that configuration values from the [llm] section are loaded correctly.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from _config_section_stub import ConfigSectionStub  # noqa: E402
from hc_config_schema import load_config  # noqa: E402


class TestLlmSectionUsesEnvAwareReader(unittest.TestCase):
    def test_llm_section_loaded_via_read_llm_section(self):
        with ConfigSectionStub(llm={"backend": "local", "host": "http://gpu:9090"}):
            cfg = load_config()
        self.assertEqual(cfg.llm.backend, "local")
        self.assertEqual(cfg.llm.host, "http://gpu:9090")


if __name__ == "__main__":
    unittest.main()
