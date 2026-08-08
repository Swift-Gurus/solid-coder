"""Tests for pre_write_gate.py — the claude backend requires ANTHROPIC_API_KEY before any check runs."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from _gate_fixtures import FM, HC, LONG_SWIFT, call_main, event
from llm_config import LlmConfig
from solid_coder_config import SolidCoderConfig


class TestApiKeyGuard(unittest.TestCase):
    def test_allows_without_check_when_claude_backend_and_no_api_key(self):
        stub_config = SolidCoderConfig(llm=LlmConfig(backend="claude"), code_review_on_write_enabled=True)
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, {}, clear=True), \
             patch(HC) as hc, patch(FM) as fm:
            code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_not_called()
        fm.assert_not_called()
        self.assertEqual(code, 0)

    def test_proceeds_when_local_backend_and_no_api_key(self):
        stub_config = SolidCoderConfig(llm=LlmConfig(backend="local"), code_review_on_write_enabled=True)
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, {}, clear=True), \
             patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_called_once()

    def test_proceeds_when_claude_backend_and_api_key_set(self):
        stub_config = SolidCoderConfig(llm=LlmConfig(backend="claude"), code_review_on_write_enabled=True)
        with patch("hc_config.load_config", return_value=stub_config), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}), \
             patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        hc.assert_called_once()


if __name__ == "__main__":
    unittest.main()
