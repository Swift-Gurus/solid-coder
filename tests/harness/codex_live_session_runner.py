"""Launches live Codex integration sessions against the current checkout."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from live_session_request import LiveSessionRequest
from live_session_result import LiveSessionResult
from live_session_running import LiveSessionRunning


"""
solid-name: CodexLiveSessionRunner
solid-category: adapter
solid-description: Adapts isolated Codex CLI execution with checkout plugin hooks, checkout MCP servers, model selection, authentication, and validated final output.
"""
class CodexLiveSessionRunner(LiveSessionRunning):

    def run(self, request: LiveSessionRequest) -> LiveSessionResult:
        codex_home = Path(tempfile.mkdtemp(prefix="solid-coder-live-codex-home-"))
        result_path = codex_home / "last-message.txt"
        try:
            self._write_config(codex_home, request.plugin_root)
            self._link_auth(codex_home)
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(codex_home)
            self._install_plugin(request, environment)
            event_stream = self._execute(request, environment, result_path)
            if not result_path.exists():
                raise RuntimeError("Codex session returned no final output")
            return LiveSessionResult(
                session_id=self._read_session_id(event_stream),
                final_output=result_path.read_text(encoding="utf-8"),
            )
        finally:
            shutil.rmtree(codex_home, ignore_errors=True)

    def _read_session_id(self, event_stream: str) -> str:
        for line in event_stream.splitlines():
            event = json.loads(line)
            if event.get("type") == "thread.started":
                session_id = event.get("thread_id", "")
                if session_id:
                    return session_id
        raise RuntimeError("Codex session returned no child thread ID")

    def _write_config(self, codex_home: Path, plugin_root: Path) -> None:
        (codex_home / "config.toml").write_text(
            "[features]\n"
            "plugins = true\n\n"
            "[marketplaces.solid-coder]\n"
            'source_type = "local"\n'
            f"source = {json.dumps(str(plugin_root))}\n\n"
            '[plugins."solid-coder@solid-coder"]\n'
            "enabled = true\n",
            encoding="utf-8",
        )

    def _link_auth(self, codex_home: Path) -> None:
        auth_path = Path.home() / ".codex" / "auth.json"
        if not auth_path.exists():
            raise RuntimeError(f"Codex auth file not found: {auth_path}")
        (codex_home / "auth.json").symlink_to(auth_path)

    def _install_plugin(self, request: LiveSessionRequest, environment: dict[str, str]) -> None:
        process = subprocess.run(
            ["codex", "plugin", "add", "solid-coder@solid-coder", "--json"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(request.project_root),
            env=environment,
        )
        if process.returncode != 0:
            raise RuntimeError(f"Codex plugin installation failed: {process.stderr}")

    def _execute(
        self,
        request: LiveSessionRequest,
        environment: dict[str, str],
        result_path: Path,
    ) -> str:
        pipeline_server = request.plugin_root / "mcp-server" / "pipeline" / "server.py"
        process = subprocess.run(
            [
                "codex",
                "exec",
                "--json",
                "--dangerously-bypass-approvals-and-sandbox",
                "--dangerously-bypass-hook-trust",
                "--skip-git-repo-check",
                "--model",
                request.model,
                "-c",
                'mcp_servers.pipeline.command="python3"',
                "-c",
                f"mcp_servers.pipeline.args=[{json.dumps(str(pipeline_server))}]",
                "--output-last-message",
                str(result_path),
                "-",
            ],
            input=request.prompt,
            capture_output=True,
            text=True,
            timeout=request.timeout,
            cwd=str(request.project_root),
            env=environment,
        )
        if process.returncode != 0:
            raise RuntimeError(f"Codex session failed: {process.stderr or process.stdout}")
        return process.stdout
