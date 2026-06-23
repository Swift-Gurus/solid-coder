"""
solid-description: Validates that all runner strategies properly initialize session context before execution.
solid-category: unit-test
"""

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from hc_runner_factory import (  # noqa: E402
    ClaudeRunnerStrategy,
    CodexRunnerStrategy,
    LocalRunnerStrategy,
    select_strategy,
)

_ENV_KEY = "SOLID_CODER_SESSION_TYPE"
_EXPECTED = "health_check"


def _clear_env():
    os.environ.pop(_ENV_KEY, None)


class TestStrategyApplyEnv(unittest.TestCase):
    """Each strategy sets SOLID_CODER_SESSION_TYPE when apply_env() is called."""

    def setUp(self):
        _clear_env()

    def tearDown(self):
        _clear_env()

    def test_claude_strategy_sets_session_type(self):
        ClaudeRunnerStrategy().apply_env()
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_local_strategy_sets_session_type(self):
        LocalRunnerStrategy(host="http://localhost:8080", model="local").apply_env()
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_codex_strategy_sets_session_type(self):
        CodexRunnerStrategy(model="", timeout=300, codex_home_dir="").apply_env()
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_env_not_set_before_apply_env(self):
        self.assertIsNone(os.environ.get(_ENV_KEY))


class TestSelectStrategy(unittest.TestCase):
    """select_strategy() returns the right class per backend config."""

    def tearDown(self):
        _clear_env()

    def test_claude_backend_returns_claude_strategy(self):
        with patch("hc_runner_factory.llm_backend", return_value="claude"), \
             patch("hc_runner_factory.llm_model", return_value=""):
            self.assertIsInstance(select_strategy(), ClaudeRunnerStrategy)

    def test_local_backend_returns_local_strategy(self):
        with patch("hc_runner_factory.llm_backend", return_value="local"), \
             patch("hc_runner_factory.llm_model", return_value="local"), \
             patch("hc_runner_factory.llm_host", return_value="http://localhost:8080"):
            self.assertIsInstance(select_strategy(), LocalRunnerStrategy)

    def test_codex_backend_returns_codex_strategy(self):
        with patch("hc_runner_factory.llm_backend", return_value="codex"), \
             patch("hc_runner_factory.llm_model", return_value=""), \
             patch("hc_runner_factory.bare_session_timeout", return_value=300), \
             patch("hc_runner_factory.codex_home", return_value=""):
            self.assertIsInstance(select_strategy(), CodexRunnerStrategy)

    def test_select_strategy_apply_env_sets_health_check_for_claude(self):
        with patch("hc_runner_factory.llm_backend", return_value="claude"), \
             patch("hc_runner_factory.llm_model", return_value=""):
            select_strategy().apply_env()
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_select_strategy_apply_env_sets_health_check_for_local(self):
        with patch("hc_runner_factory.llm_backend", return_value="local"), \
             patch("hc_runner_factory.llm_model", return_value="local"), \
             patch("hc_runner_factory.llm_host", return_value="http://localhost:8080"):
            select_strategy().apply_env()
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_select_strategy_apply_env_sets_health_check_for_codex(self):
        with patch("hc_runner_factory.llm_backend", return_value="codex"), \
             patch("hc_runner_factory.llm_model", return_value=""), \
             patch("hc_runner_factory.bare_session_timeout", return_value=300), \
             patch("hc_runner_factory.codex_home", return_value=""):
            select_strategy().apply_env()
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)


class TestCodeHealthCheckSetsEnv(unittest.TestCase):
    """code_health_check._check() sets SOLID_CODER_SESSION_TYPE for every backend."""

    def setUp(self):
        _clear_env()

    def tearDown(self):
        _clear_env()

    def _run_check_with_backend(self, backend: str):
        checker_mock = MagicMock()
        checker_mock.check.return_value = []
        codex_runner_mock = MagicMock()
        with patch("hc_runner_factory.llm_backend", return_value=backend), \
             patch("hc_runner_factory.llm_model", return_value=""), \
             patch("hc_runner_factory.llm_host", return_value="http://localhost:8080"), \
             patch("hc_runner_factory.bare_session_timeout", return_value=300), \
             patch("hc_runner_factory.codex_home", return_value=""), \
             patch("hc_runner_factory.make_llama_server_runner", return_value=MagicMock()), \
             patch("hc_codex_runner.make_codex_runner", return_value=codex_runner_mock), \
             patch("code_health_check.make_health_checker", return_value=checker_mock), \
             patch("code_health_check.build_mcp_config", return_value=""):
            import code_health_check
            code_health_check._check("content", "/f.swift", "Swift", "sid")

    def test_claude_backend_sets_session_type(self):
        self._run_check_with_backend("claude")
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_local_backend_sets_session_type(self):
        self._run_check_with_backend("local")
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_codex_backend_sets_session_type(self):
        self._run_check_with_backend("codex")
        self.assertEqual(os.environ.get(_ENV_KEY), _EXPECTED)

    def test_env_not_set_before_check(self):
        self.assertIsNone(os.environ.get(_ENV_KEY))


if __name__ == "__main__":
    unittest.main()
