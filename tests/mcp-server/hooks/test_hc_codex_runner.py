"""
solid-description: Validates isolated Codex health-check command construction, execution, cleanup, and factory wiring.
solid-category: unit-test
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from codex_command_builder import CodexCommandBuilder  # noqa: E402
from codex_command_executor import CodexCommandExecutor  # noqa: E402
from codex_execution_validator import CodexExecutionValidator  # noqa: E402
from codex_mcp_config_argument_builder import CodexMcpConfigArgumentBuilder  # noqa: E402
from codex_prompt_artifact_user import CodexPromptArtifactUser  # noqa: E402
from codex_prompt_executor import CodexPromptExecutor  # noqa: E402
from codex_temp_file_manager import CodexTempFileManager  # noqa: E402
from hc_codex_runner import CodexRunner, make_codex_runner  # noqa: E402
from hook_utils import SubprocessError  # noqa: E402
from llama.json_deserializer import JsonDeserializer  # noqa: E402
from llama.json_serializer import JsonSerializer  # noqa: E402
from subprocess_error_factory import SubprocessErrorFactory  # noqa: E402
from test_utils import TempDirTestBase  # noqa: E402


_MCP_CONFIG = """{
  "mcpServers": {
    "pipeline": {"command": "python3", "args": ["/repo/pipeline.py"]},
    "docs": {"command": "python3", "args": ["/repo/docs.py"]}
  }
}"""


def _config_argument_builder() -> CodexMcpConfigArgumentBuilder:
    return CodexMcpConfigArgumentBuilder(
        deserializer=JsonDeserializer(),
        serializer=JsonSerializer(),
    )


def _command_builder(model: str = "o4-mini", mcp_config: str = _MCP_CONFIG) -> CodexCommandBuilder:
    return CodexCommandBuilder(
        model=model,
        mcp_config=mcp_config,
        config_argument_builder=_config_argument_builder(),
    )


def _prompt_executor(subprocess_runner, cwd: str = "") -> CodexPromptExecutor:
    return CodexPromptExecutor(
        command_builder=_command_builder(),
        artifact_user=CodexPromptArtifactUser(prompt_session=CodexTempFileManager()),
        command_executor=CodexCommandExecutor(
            subprocess_runner=subprocess_runner,
            execution_validator=CodexExecutionValidator(
                error_factory=SubprocessErrorFactory(),
            ),
            logger=MagicMock(),
        ),
        cwd=cwd,
    )


def _subprocess_with_result(result_text: str):
    subprocess_runner = MagicMock()

    def run(command, timeout=None, stdin=None, cwd=None):
        result_index = command.index("--output-last-message") + 1
        Path(command[result_index]).write_text(result_text, encoding="utf-8")
        return True, "", ""

    subprocess_runner.run.side_effect = run
    return subprocess_runner


class TestCodexMcpConfigArgumentBuilder(unittest.TestCase):
    def test_builds_inline_overrides_for_every_server(self):
        arguments = _config_argument_builder().build(_MCP_CONFIG)

        self.assertIn('mcp_servers.pipeline.command="python3"', arguments)
        self.assertIn('mcp_servers.pipeline.args=["/repo/pipeline.py"]', arguments)
        self.assertIn('mcp_servers.docs.command="python3"', arguments)
        self.assertIn('mcp_servers.docs.args=["/repo/docs.py"]', arguments)
        self.assertEqual(arguments.count("-c"), 8)

    def test_configured_servers_are_required_before_model_execution(self):
        arguments = _config_argument_builder().build(_MCP_CONFIG)

        for server in ("pipeline", "docs"):
            with self.subTest(server=server):
                self.assertIn(f"mcp_servers.{server}.required=true", arguments)
                self.assertIn(f"mcp_servers.{server}.startup_timeout_sec=30", arguments)

    def test_real_gate_profile_requires_the_flow_server_without_changing_shared_json(self):
        from mcp_config_builder import McpConfigBuilder
        from mcp_config_profile import McpConfigProfile

        configuration = McpConfigBuilder(
            Path("/plugin/root"), McpConfigProfile.GATE_FLOW, JsonSerializer(),
        ).build()
        command = _command_builder(mcp_config=configuration).build(Path("/tmp/result.txt"))

        self.assertIn("mcp_servers.solid-coder-flow-engine.required=true", command)
        self.assertIn("mcp_servers.solid-coder-flow-engine.startup_timeout_sec=30", command)
        self.assertNotIn("required", configuration)
        self.assertNotIn("startup_timeout_sec", configuration)

    def test_empty_configuration_adds_no_overrides(self):
        self.assertEqual(_config_argument_builder().build(""), [])


class TestCodexCommandBuilder(unittest.TestCase):
    def test_isolates_execution_from_persistent_user_configuration(self):
        command = _command_builder().build(Path("/tmp/result.txt"))

        self.assertIn("--ignore-user-config", command)
        self.assertNotIn("--profile", command)

    def test_includes_model_and_output_path(self):
        command = _command_builder(model="gpt-5.6-terra").build(Path("/tmp/out.txt"))

        self.assertEqual(command[command.index("--model") + 1], "gpt-5.6-terra")
        self.assertEqual(command[command.index("--output-last-message") + 1], "/tmp/out.txt")

    def test_omits_model_when_empty(self):
        command = _command_builder(model="").build(Path("/tmp/result.txt"))

        self.assertNotIn("--model", command)


class TestCodexRunner(unittest.TestCase):
    def test_delegates_prompt_execution(self):
        prompt_executor = MagicMock()
        prompt_executor.execute.return_value = "Findings submitted."

        result = CodexRunner(prompt_executor=prompt_executor).run("prompt", timeout=30)

        self.assertEqual(result, "Findings submitted.")
        prompt_executor.execute.assert_called_once_with("prompt", 30)


class TestCodexPromptExecution(TempDirTestBase):
    def test_returns_last_message_and_passes_prompt_via_stdin(self):
        observed_prompts = []
        subprocess_runner = _subprocess_with_result("Findings submitted.")
        original_run = subprocess_runner.run.side_effect

        def capture(command, timeout=None, stdin=None, cwd=None):
            observed_prompts.append(stdin.read())
            return original_run(command, timeout=timeout, stdin=stdin, cwd=cwd)

        subprocess_runner.run.side_effect = capture

        result = _prompt_executor(subprocess_runner).execute("my prompt text", timeout=30)

        self.assertEqual(result, "Findings submitted.")
        self.assertEqual(observed_prompts, ["my prompt text"])

    def test_raises_on_nonzero_exit(self):
        subprocess_runner = MagicMock()
        subprocess_runner.run.return_value = False, "", "crashed"

        with self.assertRaises(SubprocessError):
            _prompt_executor(subprocess_runner).execute("prompt", timeout=30)

    def test_forwards_configured_cwd(self):
        subprocess_runner = _subprocess_with_result("ok")

        _prompt_executor(subprocess_runner, cwd="/Users/alex/Developer/build-mobile").execute(
            "prompt",
            timeout=30,
        )

        self.assertEqual(
            subprocess_runner.run.call_args.kwargs["cwd"],
            "/Users/alex/Developer/build-mobile",
        )

    def test_empty_cwd_is_forwarded_as_none(self):
        subprocess_runner = _subprocess_with_result("ok")

        _prompt_executor(subprocess_runner, cwd="").execute("prompt", timeout=30)

        self.assertIsNone(subprocess_runner.run.call_args.kwargs["cwd"])


class TestMakeCodexRunner(TempDirTestBase):
    def test_retains_child_output_in_the_target_project_audit_directory(self):
        process = _subprocess_with_result("Reviewed")
        run = process.run.side_effect

        def completed(*arguments, **keywords):
            run(*arguments, **keywords)
            return True, '{"thread_id":"child-session"}', "server startup warning"

        process.run.side_effect = completed
        audit = self.output_dir / "audit"
        with (
            patch("hc_codex_runner.SubprocessAdapter", return_value=process),
            patch("hc_codex_runner.solid_coder_project_dir", return_value=audit) as project_audit,
        ):
            result = make_codex_runner(cwd="/target/project").run("prompt", timeout=30)

        self.assertEqual(result, "Reviewed")
        project_audit.assert_called_with(Path("/target/project"))
        diagnostics = (audit / "codex-execution.log").read_text()
        self.assertIn('codex.stdout {"thread_id":"child-session"}', diagnostics)
        self.assertIn("codex.stderr server startup warning", diagnostics)

    def test_returns_runner_without_writing_persistent_profile(self):
        runner = make_codex_runner(mcp_config=_MCP_CONFIG)

        self.assertIsInstance(runner, CodexRunner)
        self.assertEqual(list(self.output_dir.iterdir()), [])

    def test_factory_returns_codex_runner_for_codex_backend(self):
        from hc_runner_factory import make_llm_runner
        from llm_config import LlmConfig
        from solid_coder_config import SolidCoderConfig

        stub_config = SolidCoderConfig(llm=LlmConfig(
            backend="codex",
            model="o4-mini",
            timeout=300,
            codex_home=str(self.output_dir),
        ))
        with patch("hc_config.SolidCoderConfigLoader.load", return_value=stub_config):
            runner = make_llm_runner(mcp_config=_MCP_CONFIG, allowed_tools="")

        self.assertIsInstance(runner, CodexRunner)
        self.assertEqual(list(self.output_dir.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
