"""
solid-name: test_mcp_request_context_session_reader
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests bridging the Claude and Codex conventions for carrying the current MCP request's session identifier.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.mcp_request_context_session_reader import McpRequestContextSessionReader


class StubCallMetaProvider:
    def __init__(self, meta: dict) -> None:
        self._meta = meta

    def get_current_call_meta(self) -> dict:
        return self._meta


class TestMcpRequestContextSessionReader(unittest.TestCase):

    def test_prefers_the_claude_env_var_over_call_meta(self):
        sut = McpRequestContextSessionReader(
            call_meta_provider=StubCallMetaProvider({"threadId": "codex-thread"}),
            env={"CLAUDE_CODE_SESSION_ID": "claude-session"},
        )

        self.assertEqual(sut.read_session_id(), "claude-session")

    def test_falls_back_to_codex_thread_id_when_no_env_var(self):
        sut = McpRequestContextSessionReader(
            call_meta_provider=StubCallMetaProvider({"threadId": "codex-thread"}),
            env={},
        )

        self.assertEqual(sut.read_session_id(), "codex-thread")

    def test_falls_back_to_codex_turn_metadata_session_id(self):
        sut = McpRequestContextSessionReader(
            call_meta_provider=StubCallMetaProvider(
                {"x-codex-turn-metadata": {"session_id": "codex-turn-session"}}
            ),
            env={},
        )

        self.assertEqual(sut.read_session_id(), "codex-turn-session")

    def test_returns_empty_string_when_nothing_is_available(self):
        sut = McpRequestContextSessionReader(
            call_meta_provider=StubCallMetaProvider({}),
            env={},
        )

        self.assertEqual(sut.read_session_id(), "")

    def test_returns_empty_string_when_call_meta_is_none(self):
        sut = McpRequestContextSessionReader(
            call_meta_provider=StubCallMetaProvider(None),
            env={},
        )

        self.assertEqual(sut.read_session_id(), "")

    def test_returns_empty_string_when_codex_turn_metadata_is_not_a_dict(self):
        sut = McpRequestContextSessionReader(
            call_meta_provider=StubCallMetaProvider({"x-codex-turn-metadata": "not-a-dict"}),
            env={},
        )

        self.assertEqual(sut.read_session_id(), "")

    def test_uses_real_os_environ_by_default_when_env_not_injected(self):
        sut = McpRequestContextSessionReader(call_meta_provider=StubCallMetaProvider({}))

        with patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "real-env-session"}, clear=True):
            self.assertEqual(sut.read_session_id(), "real-env-session")


if __name__ == "__main__":
    unittest.main()
