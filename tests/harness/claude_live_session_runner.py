"""Launches live Claude integration sessions against the current checkout."""

from __future__ import annotations

import json
import subprocess

from live_session_request import LiveSessionRequest
from live_session_result import LiveSessionResult
from live_session_running import LiveSessionRunning


"""
solid-name: ClaudeLiveSessionRunner
solid-category: adapter
solid-description: Adapts Claude Code CLI execution with checkout plugin loading, explicit MCP configuration, model selection, and validated final output.
"""
class ClaudeLiveSessionRunner(LiveSessionRunning):

    def run(self, request: LiveSessionRequest) -> LiveSessionResult:
        command = [
            "claude",
            "-p",
            request.prompt,
            "--output-format",
            "json",
            "--model",
            request.model,
            "--mcp-config",
            request.mcp_config,
            "--allowedTools",
            request.allowed_tools,
            "--plugin-dir",
            str(request.plugin_root),
        ]
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=request.timeout,
            cwd=str(request.project_root),
            stdin=subprocess.DEVNULL,
        )
        if process.returncode != 0:
            raise RuntimeError(f"Claude session failed: {process.stderr or process.stdout}")
        if not process.stdout:
            raise RuntimeError("Claude session returned no final output")
        return self._parse_result(process.stdout)

    def _parse_result(self, raw_output: str) -> LiveSessionResult:
        payload: object = json.loads(raw_output)
        result_event = None
        if isinstance(payload, dict):
            result_event = payload
        elif isinstance(payload, list):
            result_event = next(
                (
                    event
                    for event in reversed(payload)
                    if isinstance(event, dict) and event.get("type") == "result"
                ),
                None,
            )
        if result_event is None:
            raise RuntimeError("Claude session returned no result event")
        session_id = result_event.get("session_id", "")
        if not session_id:
            raise RuntimeError("Claude session returned no session ID")
        return LiveSessionResult(
            session_id=session_id,
            final_output=result_event.get("result", ""),
        )
