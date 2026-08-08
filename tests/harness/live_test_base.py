"""Provides caller-session context shared by live integration-test backends."""

from __future__ import annotations

import os


"""
solid-name: LiveTestBase
solid-category: test-support
solid-description: Resolves the real parent session that launched a live test independently from the backend selected for its child session.
"""
class LiveTestBase:

    @property
    def parent_session_id(self) -> str:
        claude_session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        if claude_session_id:
            return claude_session_id

        codex_thread_id = os.environ.get("CODEX_THREAD_ID", "")
        if codex_thread_id:
            return codex_thread_id

        raise RuntimeError(
            "Live tests require CLAUDE_CODE_SESSION_ID or CODEX_THREAD_ID"
        )
