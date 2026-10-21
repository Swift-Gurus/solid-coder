"""Checks the real delegate composition at the model-runner boundary."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.project_context import ProjectDirectory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: TestSessionDelegateCapabilitiesIntegration
solid-category: integration-test
solid-spec: [SPEC-027, SPEC-067]
solid-description: Verifies that production-composed child sessions receive the flow-engine server and its callable tool names.
"""
class TestSessionDelegateCapabilitiesIntegration(unittest.TestCase):
    def test_default_session_uses_flow_engine_not_legacy_review_servers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            workflow = project / "workflow.yaml"
            workflow.write_text(
                "name: delegate_capabilities\n"
                "steps:\n"
                "  - id: child\n"
                "    type: delegate\n"
                "    mode: session\n"
                "    prompt: Run the child workflow and return its value.\n"
                "    outputs:\n"
                "      - name: child_value\n"
                "        type: data\n"
                "        schema: {type: integer}\n",
                encoding="utf-8",
            )
            engine = FlowRunOrchestratorFactory(
                base_dir_resolver=RunsBaseDirResolver(
                    project_dir_fn=lambda: project,
                ),
                project_directory=ProjectDirectory(path=project),
                plugin_root=_PROJECT_ROOT,
            ).build()

            with patch("hc_runner_factory.select_strategy") as select_strategy:
                runner_factory = select_strategy.return_value.make_runner
                runner_factory.return_value.run.return_value = '{"child_value": 42}'
                result = engine.flow_start(str(workflow))

            self.assertEqual(result.status, "done")
            runner_factory.assert_called_once()
            arguments = runner_factory.call_args.kwargs
            servers = json.loads(arguments["mcp_config"])["mcpServers"]
            self.assertEqual(list(servers), ["solid-coder-flow-engine"])
            self.assertEqual(
                servers["solid-coder-flow-engine"]["args"],
                [str(_PROJECT_ROOT / "mcp-server/flow_engine/server.py")],
            )
            self.assertEqual(
                arguments["allowed_tools"].split(","),
                [
                    "mcp__solid-coder-flow-engine__flow_start",
                    "mcp__solid-coder-flow-engine__flow_next",
                ],
            )
