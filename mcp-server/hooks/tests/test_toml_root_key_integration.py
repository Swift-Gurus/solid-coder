"""
solid-description: Validates that configuration settings control whether code review runs on write.
solid-category: unit-test
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from _gate_fixtures import FM, HC, LONG_SWIFT, call_main, event
from test_utils import write_toml


class TestTomlRootKeyIntegration(unittest.TestCase):
    """End-to-end: a real .solid-coder/config.toml file on disk drives the gate, with no
    config mocking — only the LLM call itself (HC/FM) is mocked.

    Regression coverage: read_section/read_root_section previously ignored CLAUDE_PROJECT_DIR
    and fell back to the plugin's own install directory, so root-level and [hooks]/[inference]/
    [server] keys never picked up the real project's config file.
    """

    def _run_with_real_toml(self, toml_content: str, env: dict):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            write_toml(tmp_path, toml_content)
            full_env = {"CLAUDE_PROJECT_DIR": str(tmp_path), **env}
            with patch.dict(os.environ, full_env, clear=True), \
                 patch(HC, return_value=[]) as hc, patch(FM) as fm:
                code, out = call_main(event("Write", "/src/Foo.swift", LONG_SWIFT))
        return code, out, hc, fm

    def test_flag_true_in_real_toml_runs_health_check(self):
        _, _, hc, _ = self._run_with_real_toml(
            'code_review_on_write_enabled = true\n\n[llm]\nbackend = "claude"\n',
            {"ANTHROPIC_API_KEY": "sk-test"},
        )
        hc.assert_called_once()

    def test_flag_false_in_real_toml_skips_health_check(self):
        _, _, hc, fm = self._run_with_real_toml(
            'code_review_on_write_enabled = false\n\n[llm]\nbackend = "claude"\n',
            {"ANTHROPIC_API_KEY": "sk-test"},
        )
        hc.assert_not_called()
        fm.assert_not_called()

    def test_flag_absent_in_real_toml_defaults_to_skip(self):
        _, _, hc, fm = self._run_with_real_toml(
            '[llm]\nbackend = "claude"\n',
            {"ANTHROPIC_API_KEY": "sk-test"},
        )
        hc.assert_not_called()
        fm.assert_not_called()

    def test_flag_nested_under_wrong_table_does_not_silently_enable(self):
        """Regression for the exact real-world mistake: placing the key after
        [hooks.pre_write_gate] nests it under that table (extra=forbid) instead of
        the root — must not silently proceed as if the flag were enabled."""
        _, out, hc, _ = self._run_with_real_toml(
            '[hooks.pre_write_gate]\nexclude = []\ncode_review_on_write_enabled = true\n\n'
            '[llm]\nbackend = "claude"\n',
            {"ANTHROPIC_API_KEY": "sk-test"},
        )
        hc.assert_not_called()
        self.assertIn("deny", out)


if __name__ == "__main__":
    unittest.main()
