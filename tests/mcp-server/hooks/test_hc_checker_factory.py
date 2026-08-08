"""solid-description: Unit tests verifying the health checker factory produces independent, configurable checker instances.
solid-category: unit-test
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from hc_checker_factory import make_health_checker
from llm_config import LlmConfig
from solid_coder_config import SolidCoderConfig


class TestMakeHealthChecker(unittest.TestCase):
    def _make_checker(self, log_path: Path | None = None):
        with patch("hc_config.load_config", return_value=SolidCoderConfig(llm=LlmConfig(backend="claude"))), \
             patch("hook_utils.subprocess.run") as sub:
            sub.return_value = MagicMock(returncode=0, stdout='{"candidate_tags": []}')
            return make_health_checker(mcp_config='{"mcpServers": {}}', log_path=log_path)

    def test_returns_object_with_check_method(self):
        checker = self._make_checker()
        self.assertTrue(callable(getattr(checker, "check", None)))

    def test_uses_default_log_path_when_none(self):
        checker = self._make_checker(log_path=None)
        self.assertIsNotNone(checker)

    def test_uses_provided_log_path(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "test.log"
            checker = self._make_checker(log_path=log_path)
            self.assertIsNotNone(checker)

    def test_different_calls_produce_independent_checkers(self):
        checker_a = self._make_checker()
        checker_b = self._make_checker()
        self.assertIsNot(checker_a, checker_b)


if __name__ == "__main__":
    unittest.main()
