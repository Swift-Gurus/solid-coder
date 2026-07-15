"""Tests for pre_write_gate.py — the code_review_on_write_enabled root config toggle."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from _gate_fixtures import FM, HC, LONG_SWIFT, call_main, event
from llm_config import LlmConfig
from solid_coder_config import SolidCoderConfig


class TestWriteReviewToggle(unittest.TestCase):
    def test_allows_without_check_when_disabled(self):
        stub_config = SolidCoderConfig(llm=LlmConfig(backend="claude"), code_review_on_write_enabled=False)
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}), \
             patch(HC) as hc, patch(FM) as fm:
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_not_called()
        fm.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_proceeds_when_enabled_and_key_present(self):
        stub_config = SolidCoderConfig(llm=LlmConfig(backend="claude"), code_review_on_write_enabled=True)
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}), \
             patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_called_once()

    def test_allows_without_check_when_enabled_but_no_api_key(self):
        stub_config = SolidCoderConfig(llm=LlmConfig(backend="claude"), code_review_on_write_enabled=True)
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, {}, clear=True), \
             patch(HC) as hc, patch(FM) as fm:
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_not_called()
        fm.assert_not_called()
        self.assertEqual(code, 0)


class TestDefaultToggleAcrossBackends(unittest.TestCase):
    """With no code_review_on_write_enabled key configured, the gate skips regardless of backend or API key."""

    def _assert_skips_by_default(self, backend, env):
        stub_config = SolidCoderConfig(llm=LlmConfig(backend=backend))
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, env, clear=True), \
             patch(HC) as hc, patch(FM) as fm:
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_not_called()
        fm.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_claude_backend_no_key(self):
        self._assert_skips_by_default("claude", {})

    def test_claude_backend_with_key_present(self):
        self._assert_skips_by_default("claude", {"ANTHROPIC_API_KEY": "sk-test"})

    def test_local_backend(self):
        self._assert_skips_by_default("local", {})

    def test_codex_backend(self):
        self._assert_skips_by_default("codex", {})

    def test_codex_backend_with_flag_enabled_proceeds_without_credential_check(self):
        """Known gap: ApiKeyGuard has no Codex credential check, so enabling the flag with
        backend=codex proceeds straight to the health check regardless of Codex auth state."""
        stub_config = SolidCoderConfig(llm=LlmConfig(backend="codex"), code_review_on_write_enabled=True)
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, {}, clear=True), \
             patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_called_once()


if __name__ == "__main__":
    unittest.main()
