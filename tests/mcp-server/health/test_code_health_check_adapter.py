"""Verifies patch context is bound without degrading the health-check contract."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER_DIRECTORY = _REPOSITORY_ROOT / "mcp-server"
for _directory in (
    _MCP_SERVER_DIRECTORY,
    _MCP_SERVER_DIRECTORY / "health",
    _MCP_SERVER_DIRECTORY / "health" / "codex",
    _MCP_SERVER_DIRECTORY / "health" / "config",
    _MCP_SERVER_DIRECTORY / "health" / "llm",
    _MCP_SERVER_DIRECTORY / "gate",
    _MCP_SERVER_DIRECTORY / "output",
    _MCP_SERVER_DIRECTORY / "patch",
    _MCP_SERVER_DIRECTORY / "session",
    _MCP_SERVER_DIRECTORY / "utils",
):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from code_health_check_adapter import CodeHealthCheckAdapter  # noqa: E402


"""
solid-name: TestCodeHealthCheckAdapter
solid-category: unit-test
solid-spec: [SPEC-049]
solid-description: Proves patch-context adaptation preserves the injected health-checking object.
"""
class TestCodeHealthCheckAdapter(unittest.TestCase):

    def test_delegates_to_the_health_checker_object(self) -> None:
        checker = MagicMock()
        checker.check.return_value = []
        patch_context = MagicMock()
        adapter = CodeHealthCheckAdapter(
            checker=checker,
            patch_context=patch_context,
        )

        result = adapter.check(
            content="final class Example {}",
            path="/project/Example.swift",
            language="Swift",
            parent_session_id="parent-session",
            cwd="/project",
        )

        self.assertEqual(result, [])
        checker.check.assert_called_once_with(
            "final class Example {}",
            "/project/Example.swift",
            "Swift",
            "parent-session",
            "/project",
            patch_context=patch_context,
        )


if __name__ == "__main__":
    unittest.main()
