"""Exercises actual MCP subprocess launches without a model session."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from health.config.mcp_config_builder import McpConfigBuilder
from json_serializer import JsonSerializer
from mcp_config_profile import McpConfigProfile

ROOT = Path(__file__).resolve().parents[4]


"""
solid-name: TestMcpRuntimeIntegration
solid-category: integration-test
solid-description: Verifies real plugin and delegated MCP launches initialize and expose tools independently of the host's default Python.
"""


class TestMcpRuntimeIntegration(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="mcp runtime ")
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.executable = str(
            Path(os.environ.get("DESKTOP_PYTHON", sys._base_executable)).absolute()
        )
        runtime_bin = Path(self.executable).parent
        self.environment = os.environ.copy()
        self.environment["PATH"] = f"{runtime_bin}:/usr/bin:/bin"
        self.environment["CLAUDE_PROJECT_DIR"] = str(self.workspace)
        for key in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"):
            self.environment.pop(key, None)
        self.environment.pop("SOLID_CODER_HEALTH_INPUT_PATH", None)
        self.environment.pop("SOLID_CODER_HEALTH_OUTPUT_PATH", None)

    def _exchange(self, server: SimpleNamespace) -> list[SimpleNamespace]:
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
        arguments = []
        for argument in server.args:
            argument = argument.replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT))
            if not argument.startswith("-") and (ROOT / argument).is_file():
                argument = str(ROOT / argument)
            arguments.append(argument)
        completed = subprocess.run(
            [server.command, *arguments],
            input="".join(json.dumps(message) + "\n" for message in messages),
            text=True,
            capture_output=True,
            timeout=30,
            cwd=self.workspace,
            env=self.environment,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return [
            json.loads(line, object_hook=lambda fields: SimpleNamespace(**fields))
            for line in completed.stdout.splitlines()
        ]

    def test_plugin_servers_initialize_through_distributed_configuration(self) -> None:
        configuration = json.loads(
            (ROOT / ".mcp.json").read_text(),
            object_hook=lambda fields: SimpleNamespace(**fields),
        )

        for name, server in vars(configuration.mcpServers).items():
            with self.subTest(server=name):
                responses = self._exchange(server)

                self.assertEqual([response.id for response in responses], [1, 2])
                self.assertTrue(responses[0].result.protocolVersion)
                self.assertTrue(responses[1].result.tools)

    def test_claude_manifest_servers_initialize_with_system_python_first(self) -> None:
        configuration = json.loads(
            (ROOT / ".claude-plugin" / "plugin.json").read_text(),
            object_hook=lambda fields: SimpleNamespace(**fields),
        )

        for name, server in vars(configuration.mcpServers).items():
            with self.subTest(server=name):
                command = SimpleNamespace(
                    command=server.command,
                    args=[
                        argument.replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT))
                        for argument in server.args
                    ],
                )
                responses = self._exchange(command)

                self.assertEqual([response.id for response in responses], [1, 2])
                self.assertTrue(responses[0].result.protocolVersion)
                self.assertTrue(responses[1].result.tools)

    def test_legacy_profile_launches_search_and_submission_tools(self) -> None:
        configuration = json.loads(
            McpConfigBuilder(
                ROOT,
                McpConfigProfile.LEGACY_HEALTH,
                JsonSerializer(),
                executable=self.executable,
            ).build(),
            object_hook=lambda fields: SimpleNamespace(**fields),
        )

        responses = self._exchange(configuration.mcpServers.pipeline)
        tools = {tool.name for tool in responses[1].result.tools}

        self.assertEqual([response.id for response in responses], [1, 2])
        self.assertTrue({"search_codebase", "submit_batch_findings"}.issubset(tools))

    def test_legacy_profile_launches_rule_loading_tools(self) -> None:
        configuration = json.loads(
            McpConfigBuilder(
                ROOT,
                McpConfigProfile.LEGACY_HEALTH,
                JsonSerializer(),
                executable=self.executable,
            ).build(),
            object_hook=lambda fields: SimpleNamespace(**fields),
        )

        responses = self._exchange(configuration.mcpServers.docs)

        self.assertIn("load_rules", {tool.name for tool in responses[1].result.tools})

    def test_workflow_profile_launches_flow_tools(self) -> None:
        configuration = json.loads(
            McpConfigBuilder(
                ROOT,
                McpConfigProfile.GATE_FLOW,
                JsonSerializer(),
                executable=self.executable,
            ).build(),
            object_hook=lambda fields: SimpleNamespace(**fields),
        )
        server = vars(configuration.mcpServers)["solid-coder-flow-engine"]

        responses = self._exchange(server)

        self.assertTrue(
            {"flow_start", "flow_next"}.issubset(
                {tool.name for tool in responses[1].result.tools}
            )
        )

    def test_legacy_gateway_loads_real_rules_with_system_python_first(self) -> None:
        source = "\n".join(
            [
                "import json, sys",
                "from pathlib import Path",
                f"sys.path.insert(0, {str(ROOT / 'mcp-server')!r})",
                "from health.gateway.gateway_command_runner import GatewayCommandRunner",
                f"gateway = GatewayCommandRunner(Path({str(ROOT / 'mcp-server' / 'gateway.py')!r}), timeout=30)",
                "tags = gateway.invoke('get_candidate_tags', result_key='candidate_tags')",
                "rules = gateway.invoke('load_detection_rules', extra_args=['--matched_tags', 'swiftui'])",
                "print(json.dumps({'tags': tags, 'principles': [rule['name'] for rule in rules['principles']]}))",
            ]
        )

        completed = subprocess.run(
            [self.executable, "-c", source],
            text=True,
            capture_output=True,
            timeout=60,
            cwd=self.workspace,
            env=self.environment,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(
            completed.stdout, object_hook=lambda fields: SimpleNamespace(**fields)
        )
        self.assertIn("swiftui", result.tags)
        self.assertTrue(
            {"srp", "ocp", "lsp", "isp", "dry", "swiftui"}.issubset(result.principles)
        )

    def test_distributed_write_hook_starts_without_launching_a_model(self) -> None:
        configuration = json.loads(
            (ROOT / "hooks" / "hooks.json").read_text(),
            object_hook=lambda fields: SimpleNamespace(**fields),
        )
        command = next(
            hook.command
            for entry in configuration.hooks.PreToolUse
            for hook in entry.hooks
            if "pre_write_gate.py" in hook.command
        )
        environment = self.environment.copy()
        environment["CLAUDE_PLUGIN_ROOT"] = str(ROOT)

        completed = subprocess.run(
            ["/bin/sh", "-c", command],
            input=json.dumps(
                {
                    "tool_name": "Read",
                    "tool_input": {"file_path": str(self.workspace / "Example.swift")},
                    "session_id": "runtime-integration",
                    "cwd": str(self.workspace),
                }
            ),
            text=True,
            capture_output=True,
            timeout=30,
            cwd=self.workspace,
            env=environment,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "")

    def test_invalid_config_during_gate_construction_produces_denial(self) -> None:
        config = self.workspace / ".solid-coder" / "config.toml"
        config.parent.mkdir()
        config.write_text('code_review_on_write_enabled = "not-a-boolean"\n')
        environment = self.environment.copy()
        environment["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
        configuration = json.loads((ROOT / "hooks/hooks.json").read_text())
        command = next(
            hook["command"]
            for entry in configuration["hooks"]["PreToolUse"]
            for hook in entry["hooks"]
            if "pre_write_gate.py" in hook["command"]
        )

        completed = subprocess.run(
            ["/bin/sh", "-c", command],
            input=json.dumps(
                {"tool_name": "Read", "tool_input": {}, "cwd": str(self.workspace)}
            ),
            text=True,
            capture_output=True,
            timeout=30,
            cwd=self.workspace,
            env=environment,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            json.loads(completed.stdout)["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )
