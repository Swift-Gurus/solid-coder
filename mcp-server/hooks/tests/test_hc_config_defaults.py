"""
solid-description: Verifies that the configuration system applies correct default values when no external configuration is provided.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from _config_section_stub import ConfigSectionStub  # noqa: E402
from hc_config_schema import load_config  # noqa: E402


class TestDefaults(unittest.TestCase):
    def test_defaults_when_no_config_present(self):
        with ConfigSectionStub():
            cfg = load_config()
        self.assertEqual(cfg.llm.backend, "claude")
        self.assertEqual(cfg.llm.timeout, 300)
        self.assertEqual(cfg.hooks, {})
        self.assertEqual(cfg.inference.max_tokens, 4096)
        self.assertEqual(cfg.server.port, 8080)


if __name__ == "__main__":
    unittest.main()
