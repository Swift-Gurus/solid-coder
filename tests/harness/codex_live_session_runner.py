"""Launches live Codex integration sessions against the current checkout."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from codex_transcript_token_usage_reader import CodexTranscriptTokenUsageReader
from live_session_artifact_directory_creator import LiveSessionArtifactDirectoryCreator
from live_session_request import LiveSessionRequest
from live_session_result import LiveSessionResult
from live_session_running import LiveSessionRunning
from review_comparison_stage_evidence import ReviewComparisonStageEvidence


"""
solid-name: CodexLiveSessionRunner
solid-category: adapter
solid-description: Adapts isolated Codex CLI execution with checkout plugin hooks, checkout MCP servers, model selection, authentication, and validated final output.
"""
class CodexLiveSessionRunner(LiveSessionRunning):

    def __init__(
        self,
        artifact_directory_creator: LiveSessionArtifactDirectoryCreator = LiveSessionArtifactDirectoryCreator(),
    ) -> None:
        self._artifact_directory_creator = artifact_directory_creator

    def run(self, request: LiveSessionRequest) -> LiveSessionResult:
        artifact_directory = self._artifact_directory_creator.create(
            request.plugin_root,
            "codex",
            request.artifact_scope,
        )
        codex_home = Path(tempfile.mkdtemp(prefix="solid-coder-live-codex-home-"))
        result_path = artifact_directory / "last-message.txt"
        execution_elapsed_seconds: float | None = None
        try:
            self._write_config(codex_home, request.plugin_root)
            self._link_auth(codex_home)
            environment = os.environ.copy()
            environment["CODEX_HOME"] = str(codex_home)
            self._install_plugin(request, environment, artifact_directory)
            execution_started = time.monotonic()
            event_stream = self._execute(
                request,
                environment,
                result_path,
                artifact_directory,
            )
            execution_elapsed_seconds = time.monotonic() - execution_started
            if not result_path.exists():
                raise RuntimeError("Codex session returned no final output")
            return LiveSessionResult(
                session_id=self._read_session_id(event_stream),
                final_output=result_path.read_text(encoding="utf-8"),
                artifact_directory=artifact_directory,
            )
        except Exception as error:
            raise RuntimeError(
                f"{error}. Artifacts: {artifact_directory}"
            ) from error
        finally:
            self._preserve_runtime(codex_home, artifact_directory)
            if execution_elapsed_seconds is not None:
                self._write_execution_evidence(
                    artifact_directory,
                    execution_elapsed_seconds,
                )
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
            "tool_output_token_limit = 262144\n\n"
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

    def _install_plugin(
        self,
        request: LiveSessionRequest,
        environment: dict[str, str],
        artifact_directory: Path,
    ) -> None:
        process = subprocess.run(
            ["codex", "plugin", "add", "solid-coder@solid-coder", "--json"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(request.project_root),
            env=environment,
        )
        (artifact_directory / "plugin-install.json").write_text(
            process.stdout,
            encoding="utf-8",
        )
        (artifact_directory / "plugin-install.stderr.log").write_text(
            process.stderr,
            encoding="utf-8",
        )
        if process.returncode != 0:
            raise RuntimeError(f"Codex plugin installation failed: {process.stderr}")

    def _execute(
        self,
        request: LiveSessionRequest,
        environment: dict[str, str],
        result_path: Path,
        artifact_directory: Path,
    ) -> str:
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
        (artifact_directory / "codex-events.jsonl").write_text(
            process.stdout,
            encoding="utf-8",
        )
        (artifact_directory / "codex-stderr.log").write_text(
            process.stderr,
            encoding="utf-8",
        )
        if process.returncode != 0:
            raise RuntimeError(f"Codex session failed: {process.stderr or process.stdout}")
        return process.stdout

    def _preserve_runtime(
        self,
        codex_home: Path,
        artifact_directory: Path,
    ) -> None:
        runtime_artifacts = artifact_directory / "codex-runtime"
        sessions = codex_home / "sessions"
        if sessions.exists():
            shutil.copytree(sessions, runtime_artifacts / "sessions")
        for database in codex_home.glob("state_*.sqlite*"):
            runtime_artifacts.mkdir(parents=True, exist_ok=True)
            shutil.copy2(database, runtime_artifacts / database.name)

    def _write_execution_evidence(
        self,
        artifact_directory: Path,
        elapsed_seconds: float,
    ) -> None:
        transcripts = sorted(
            (
                artifact_directory
                / "codex-runtime"
                / "sessions"
            ).rglob("*.jsonl")
        )
        if not transcripts:
            raise RuntimeError("Codex session preserved no rollout transcript")
        evidence = ReviewComparisonStageEvidence(
            elapsed_seconds=elapsed_seconds,
            token_usage=CodexTranscriptTokenUsageReader().read(transcripts[-1]),
        )
        (artifact_directory / "full-run-evidence.json").write_text(
            evidence.model_dump_json(indent=2),
            encoding="utf-8",
        )
