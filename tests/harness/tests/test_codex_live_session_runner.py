"""Verifies conversion of Codex CLI events into a typed live-session result."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from codex_live_session_runner import CodexLiveSessionRunner  # noqa: E402
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_session_request import LiveSessionRequest  # noqa: E402
from live_session_result import LiveSessionResult  # noqa: E402
from review_comparison_stage_evidence import ReviewComparisonStageEvidence  # noqa: E402


class TestCodexLiveSessionRunner(unittest.TestCase):

    def test_returns_child_thread_id_and_final_output(self) -> None:
        runner = CodexLiveSessionRunner()
        event_stream = '{"type":"thread.started","thread_id":"codex-child"}\n'

        result = self._run_with_output(runner, event_stream, "completed")

        self.assertEqual(result.session_id, "codex-child")
        self.assertEqual(result.final_output, "completed")

    def test_persists_normalized_execution_evidence(self) -> None:
        runner = CodexLiveSessionRunner()
        event_stream = '{"type":"thread.started","thread_id":"codex-child"}\n'

        evidence = self._run_with_output(
            runner,
            event_stream,
            "completed",
            read_evidence=True,
        )

        self.assertIsInstance(evidence, ReviewComparisonStageEvidence)
        self.assertEqual(evidence.elapsed_seconds, 12.5)
        self.assertTrue(evidence.token_usage.available)
        self.assertEqual(evidence.token_usage.input_tokens, 10)
        self.assertEqual(evidence.token_usage.cached_input_tokens, 4)
        self.assertEqual(evidence.token_usage.output_tokens, 2)
        self.assertEqual(evidence.token_usage.reasoning_output_tokens, 1)
        self.assertEqual(evidence.token_usage.total_tokens, 12)

    def test_preserves_raw_command_output(self) -> None:
        runner = CodexLiveSessionRunner()
        completed = CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"type":"thread.started","thread_id":"codex-child"}\n',
            stderr="diagnostic",
        )
        with tempfile.TemporaryDirectory() as directory:
            artifact_directory = Path(directory)
            with patch(
                "codex_live_session_runner.subprocess.run",
                return_value=completed,
            ):
                event_stream = runner._execute(
                    self._request(),
                    {},
                    artifact_directory / "last-message.txt",
                    artifact_directory,
                )

            self.assertEqual(event_stream, completed.stdout)
            self.assertEqual(
                (artifact_directory / "codex-events.jsonl").read_text(),
                completed.stdout,
            )
            self.assertEqual(
                (artifact_directory / "codex-stderr.log").read_text(),
                completed.stderr,
            )

    def test_execute_uses_installed_plugin_registration_without_overrides(self) -> None:
        runner = CodexLiveSessionRunner()
        completed = CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout='{"type":"thread.started","thread_id":"codex-child"}\n',
            stderr="",
        )
        with tempfile.TemporaryDirectory() as directory:
            artifact_directory = Path(directory)
            result_path = artifact_directory / "last-message.txt"
            with patch(
                "codex_live_session_runner.subprocess.run",
                return_value=completed,
            ) as process:
                runner._execute(
                    self._request(),
                    {},
                    result_path,
                    artifact_directory,
                )

        command = process.call_args.args[0]
        self.assertFalse(
            any("mcp_servers." in argument for argument in command)
        )
        environment = process.call_args.kwargs["env"]
        self.assertNotIn("CLAUDE_PROJECT_DIR", environment)
        self.assertEqual(
            environment["RUST_LOG"],
            "warn,codex_mcp=debug,codex_mcp_extension=debug,"
            "codex_core::mcp_tool_exposure=debug",
        )

    def test_rejects_event_stream_without_child_thread_id(self) -> None:
        runner = CodexLiveSessionRunner()

        with self.assertRaisesRegex(RuntimeError, "no child thread ID"):
            self._run_with_output(runner, '{"type":"turn.started"}\n', "completed")

    def test_generated_config_preserves_complete_flow_tool_responses(self) -> None:
        runner = CodexLiveSessionRunner()
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)

            runner._write_config(codex_home, Path("/plugin"))

            config = (codex_home / "config.toml").read_text(encoding="utf-8")
            self.assertIn("tool_output_token_limit = 262144", config)

    def test_generated_config_records_checkout_project_context(self) -> None:
        runner = CodexLiveSessionRunner()
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)

            runner._write_config(codex_home, Path("/plugin"))

            config = (codex_home / "config.toml").read_text(encoding="utf-8")
            self.assertIn("[[hooks.SessionStart]]", config)
            self.assertIn(
                "/plugin/mcp-server/hooks/on_agent_start.py",
                config,
            )

    def test_generated_config_enables_logs_inside_isolated_home(self) -> None:
        runner = CodexLiveSessionRunner()
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)

            runner._write_config(codex_home, Path("/plugin"))

            config = (codex_home / "config.toml").read_text(encoding="utf-8")
            self.assertIn(f'log_dir = "{codex_home / "log"}"', config)

    def test_preserves_startup_diagnostics_without_copying_credentials(self) -> None:
        runner = CodexLiveSessionRunner()
        with tempfile.TemporaryDirectory() as artifacts:
            artifact_directory = Path(artifacts)
            with tempfile.TemporaryDirectory() as directory:
                codex_home = Path(directory)
                (codex_home / "log").mkdir()
                (codex_home / "log" / "codex-tui.log").write_text("MCP startup failed")
                (codex_home / "config.toml").write_text("plugins = true")
                (codex_home / "logs_1.sqlite").write_bytes(b"database")
                (codex_home / "logs_1.sqlite-wal").write_bytes(b"pending logs")
                (codex_home / "state_5.sqlite").write_bytes(b"state")
                (codex_home / "auth.json").write_text("do not preserve credentials")

                runner._preserve_runtime(codex_home, artifact_directory)

            runtime = artifact_directory / "codex-runtime"
            self.assertEqual(
                sorted(str(path.relative_to(runtime)) for path in runtime.rglob("*") if path.is_file()),
                ["config.toml", "log/codex-tui.log", "logs_1.sqlite", "logs_1.sqlite-wal", "state_5.sqlite"],
            )
            self.assertEqual((runtime / "log" / "codex-tui.log").read_text(), "MCP startup failed")
            self.assertEqual((runtime / "logs_1.sqlite-wal").read_bytes(), b"pending logs")

    def _run_with_output(
        self,
        runner: CodexLiveSessionRunner,
        event_stream: str,
        final_output: str,
        read_evidence: bool = False,
    ) -> LiveSessionResult | ReviewComparisonStageEvidence:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_home = root / "codex-home"
            codex_home.mkdir()
            sessions = codex_home / "sessions"
            sessions.mkdir()
            (sessions / "rollout.jsonl").write_text(
                event_stream
                + '{"type":"event_msg","payload":{"type":"token_count","info":'
                '{"total_token_usage":{"input_tokens":10,"cached_input_tokens":4,'
                '"cache_write_input_tokens":0,"output_tokens":2,'
                '"reasoning_output_tokens":1,"total_tokens":12}}}}\n',
                encoding="utf-8",
            )
            (codex_home / "state_test.sqlite").write_text("state", encoding="utf-8")
            artifact_directory = root / "artifacts"
            artifact_directory.mkdir()
            result_path = artifact_directory / "last-message.txt"
            result_path.write_text(final_output, encoding="utf-8")
            with (
                patch(
                    "codex_live_session_runner.tempfile.mkdtemp",
                    return_value=str(codex_home),
                ),
                patch(
                    "codex_live_session_runner.LiveSessionArtifactDirectoryCreator.create",
                    return_value=artifact_directory,
                ) as artifact_creator,
                patch.object(runner, "_write_config"),
                patch.object(runner, "_link_auth"),
                patch.object(runner, "_install_plugin"),
                patch.object(runner, "_execute", return_value=event_stream),
                patch(
                    "codex_live_session_runner.time.monotonic",
                    side_effect=[100.0, 112.5],
                ),
            ):
                result = runner.run(self._request())

            artifact_creator.assert_called_once_with(
                Path("/plugin"),
                "codex",
                self._request().artifact_scope,
            )
            self.assertEqual(result.artifact_directory, artifact_directory)
            self.assertTrue(
                (artifact_directory / "codex-runtime" / "sessions" / "rollout.jsonl").exists()
            )
            self.assertTrue(
                (artifact_directory / "codex-runtime" / "state_test.sqlite").exists()
            )
            if read_evidence:
                return ReviewComparisonStageEvidence.model_validate_json(
                    (artifact_directory / "full-run-evidence.json").read_text(
                        encoding="utf-8"
                    )
                )
            return result

    def _request(self) -> LiveSessionRequest:
        return LiveSessionRequest(
            prompt="prompt",
            artifact_scope=LiveSessionArtifactScope(
                domain="runner",
                scenario="codex",
            ),
            project_root=Path("/project"),
            plugin_root=Path("/plugin"),
            model="model",
            timeout=10,
            allowed_tools="tools",
            mcp_config="config",
        )


if __name__ == "__main__":
    unittest.main()
