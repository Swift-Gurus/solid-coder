"""
solid-name: McpRequestContextSessionReader
solid-category: service
solid-spec: [SPEC-013]
solid-description: Retrieves the session identifier for the current request.
"""

from __future__ import annotations

import os
from typing import Optional

from call_meta_providing import CallMetaProviding

_CLAUDE_SESSION_ENV_VAR = "CLAUDE_CODE_SESSION_ID"
_CODEX_TURN_METADATA_KEY = "x-codex-turn-metadata"


class McpRequestContextSessionReader:

    def __init__(self, call_meta_provider: CallMetaProviding, env: Optional[dict] = None) -> None:
        self._call_meta_provider = call_meta_provider
        self._env = env if env is not None else os.environ

    def read_session_id(self) -> str:
        env_session_id = self._env.get(_CLAUDE_SESSION_ENV_VAR, "")
        if env_session_id:
            return env_session_id

        meta = self._call_meta_provider.get_current_call_meta() or {}
        thread_id = meta.get("threadId", "")
        if thread_id:
            return thread_id

        try:
            return meta.get(_CODEX_TURN_METADATA_KEY, {}).get("session_id", "") or ""
        except AttributeError:
            return ""
