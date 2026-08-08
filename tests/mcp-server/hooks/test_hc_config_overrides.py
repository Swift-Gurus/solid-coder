"""
solid-description: Validates that configuration overrides are correctly applied.
solid-category: unit-test
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from _config_section_stub import ConfigSectionStub  # noqa: E402
from hc_config_schema import load_config  # noqa: E402
from hook_config import HookConfig  # noqa: E402


class TestConfigOverrides(unittest.TestCase):
    def test_llm_overrides_apply(self):
        with ConfigSectionStub(llm={"backend": "local", "timeout": 120}):
            cfg = load_config()
        self.assertEqual(cfg.llm.backend, "local")
        self.assertEqual(cfg.llm.timeout, 120)

    def test_hooks_section_parses_into_hook_config(self):
        with ConfigSectionStub(hooks={"pre_write_gate": {"exclude": ["tests/fixtures/**"]}}):
            cfg = load_config()
        self.assertIsInstance(cfg.hooks["pre_write_gate"], HookConfig)
        self.assertEqual(cfg.hook_exclude("pre_write_gate"), ["tests/fixtures/**"])

    def test_hook_exclude_returns_empty_for_unconfigured_hook(self):
        with ConfigSectionStub():
            cfg = load_config()
        self.assertEqual(cfg.hook_exclude("some_other_hook"), [])

    def test_inference_overrides_apply(self):
        with ConfigSectionStub(inference={"temperature": 0.7, "max_tokens": 2048}):
            cfg = load_config()
        self.assertEqual(cfg.inference.temperature, 0.7)
        self.assertEqual(cfg.inference.max_tokens, 2048)

    def test_code_review_on_write_enabled_defaults_false(self):
        with ConfigSectionStub():
            cfg = load_config()
        self.assertFalse(cfg.code_review_on_write_enabled)

    def test_code_review_on_write_enabled_override_applies(self):
        with ConfigSectionStub(root={"code_review_on_write_enabled": True}):
            cfg = load_config()
        self.assertTrue(cfg.code_review_on_write_enabled)


if __name__ == "__main__":
    unittest.main()
