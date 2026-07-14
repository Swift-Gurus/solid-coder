"""Tests for validate_swift_frontmatter.fix() — the LLM correction call."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

import validate_swift_frontmatter as hook
from _frontmatter_fixtures import BAD_CONTENT, CLEAN_CONTENT, llm_raw, mock_runner


class TestFix(unittest.TestCase):
    def test_returns_corrected_content_from_llm(self):
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=mock_runner(llm_raw(CLEAN_CONTENT))):
            result = hook.fix(BAD_CONTENT)
        self.assertEqual(result, CLEAN_CONTENT)

    def test_returns_unchanged_content_when_llm_echoes_back(self):
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=mock_runner(llm_raw(CLEAN_CONTENT))):
            result = hook.fix(CLEAN_CONTENT)
        self.assertEqual(result, CLEAN_CONTENT)

    def test_raises_when_runner_raises(self):
        from hook_utils import SubprocessError
        runner = MagicMock()
        runner.run.side_effect = SubprocessError("subprocess died")
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner):
            with self.assertRaises(SubprocessError):
                hook.fix(BAD_CONTENT)

    def test_returns_none_when_llm_returns_plain_text_instead_of_json(self):
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=mock_runner(CLEAN_CONTENT)):
            self.assertIsNone(hook.fix(BAD_CONTENT))

    def test_includes_parent_session_header_in_prompt(self):
        captured_prompts = []
        runner = MagicMock()
        runner.run.side_effect = lambda prompt, **kw: (captured_prompts.append(prompt), llm_raw(CLEAN_CONTENT))[1]
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner):
            hook.fix(BAD_CONTENT, parent_session_id="sess-123")
        self.assertIn("spawned-by: sess-123", captured_prompts[0])

    def test_runner_called_with_bare_session_timeout(self):
        from llm_config import LlmConfig
        from solid_coder_config import SolidCoderConfig
        runner = MagicMock()
        runner.run.return_value = llm_raw(CLEAN_CONTENT)
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner), \
             patch("hc_config.load_config", return_value=SolidCoderConfig(llm=LlmConfig(bare_session_timeout=42))):
            hook.fix(BAD_CONTENT)
        _, kwargs = runner.run.call_args
        self.assertEqual(kwargs.get("timeout"), 42)

    def test_runner_created_with_no_mcp_config(self):
        runner = MagicMock()
        runner.run.return_value = llm_raw(CLEAN_CONTENT)
        with patch("validate_swift_frontmatter.make_llm_runner", return_value=runner) as mock_factory:
            hook.fix(BAD_CONTENT)
        _, kwargs = mock_factory.call_args
        self.assertEqual(kwargs.get("mcp_config"), "")


if __name__ == "__main__":
    unittest.main()
