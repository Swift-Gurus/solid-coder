"""solid-description: Unit tests verifying the health checker factory produces independent, configurable checker instances.
solid-category: unit-test
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from code_health_check_request import CodeHealthCheckRequest
from hc_checker_factory import LegacyHealthCheckerFactory
from llm_config import LlmConfig
from solid_coder_config import SolidCoderConfig


class TestLegacyHealthCheckerFactory(unittest.TestCase):
    def setUp(self):
        self.project_root = Path("/project")
        self.strategy = MagicMock()
        self.factory = LegacyHealthCheckerFactory(
            project_root=self.project_root,
            config=SolidCoderConfig(llm=LlmConfig(backend="claude")),
            strategy=self.strategy,
            mcp_config='{"mcpServers": {}}',
        )

    def _make_checker(self):
        return self.factory.make(CodeHealthCheckRequest(
            content="class Example {}",
            path="/project/Example.swift",
            language="Swift",
            parent_session_id="parent-123",
        ))

    def test_returns_object_with_check_method(self):
        checker = self._make_checker()
        self.assertTrue(callable(getattr(checker, "check", None)))

    def test_passes_request_context_to_runner(self):
        self._make_checker()

        self.strategy.make_runner.assert_called_once_with(
            mcp_config='{"mcpServers": {}}',
            allowed_tools=unittest.mock.ANY,
            session_id="parent-123",
            file_path="/project/Example.swift",
            cwd="/project",
        )

    def test_different_calls_produce_independent_checkers(self):
        checker_a = self._make_checker()
        checker_b = self._make_checker()
        self.assertIsNot(checker_a, checker_b)


if __name__ == "__main__":
    unittest.main()
