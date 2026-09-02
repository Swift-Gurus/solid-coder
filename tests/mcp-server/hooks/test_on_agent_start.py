"""Verifies SessionStart captures project context for plugin MCP requests."""

import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIRECTORY = _REPOSITORY_ROOT / "mcp-server" / "hooks"
if str(_HOOKS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIRECTORY))

import on_agent_start  # noqa: E402


"""
solid-name: TestOnAgentStart
solid-category: unit-test
solid-description: Proves SessionStart records project context for every session while preserving managed-session registration.
"""
class TestOnAgentStart(unittest.TestCase):

    def test_records_project_context_without_managed_session_type(self) -> None:
        event = json.dumps({"session_id": "session-1", "cwd": "/project"})
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(sys, "stdin", io.StringIO(event)),
            patch.object(
                on_agent_start,
                "SessionProjectContextPathResolver",
                create=True,
            ) as path_resolver_type,
            patch.object(
                on_agent_start,
                "SessionProjectDirectoryRecorder",
                create=True,
            ) as recorder_type,
            patch.object(on_agent_start, "register_session") as register_session,
        ):
            on_agent_start.main()

        recorder_type.assert_called_once_with(path_resolver_type.return_value.resolve)
        recorder_type.return_value.record.assert_called_once_with(
            "session-1",
            Path("/project"),
        )
        register_session.assert_not_called()

    def test_preserves_managed_session_registration(self) -> None:
        event = json.dumps({"session_id": "session-2", "cwd": "/project"})
        with (
            patch.dict(
                os.environ,
                {"SOLID_CODER_SESSION_TYPE": "health_check"},
                clear=True,
            ),
            patch.object(sys, "stdin", io.StringIO(event)),
            patch.object(
                on_agent_start,
                "SessionProjectContextPathResolver",
                create=True,
            ),
            patch.object(
                on_agent_start,
                "SessionProjectDirectoryRecorder",
                create=True,
            ),
            patch.object(on_agent_start, "register_session") as register_session,
        ):
            on_agent_start.main()

        register_session.assert_called_once_with(
            session_id="session-2",
            session_type="health_check",
            cwd="/project",
        )


if __name__ == "__main__":
    unittest.main()
