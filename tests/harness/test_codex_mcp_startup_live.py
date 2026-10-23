"""Exercises required MCP startup through the production Codex child runner."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from codex_test_base import CodexTestBase
from harness_factory import HookUtilsTomlLoader
from hc_codex_runner import make_codex_runner
from hook_utils import solid_coder_project_dir
from json_serializer import JsonSerializer
from live_session_artifact_directory_creator import LiveSessionArtifactDirectoryCreator
from live_session_artifact_scope import LiveSessionArtifactScope
from llm_config import LlmConfig
from mcp_config_builder import McpConfigBuilder
from mcp_config_profile import McpConfigProfile
from model_profile_loader import ModelProfileLoader
from subprocess_error import SubprocessError

"""
solid-name: TestCodexMcpStartupLive
solid-category: integration-test
solid-spec: [SPEC-067]
solid-description: Proves a delegated Codex session waits for delayed required capabilities and fails before model work when initialization fails.
"""


class TestCodexMcpStartupLive(CodexTestBase, unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="solid-coder-mcp-startup-")
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        self.audit = solid_coder_project_dir(self.project)
        profile = ModelProfileLoader(_PROJECT_ROOT, HookUtilsTomlLoader()).load(
            self.MODEL_PROFILE
        )
        self.llm = LlmConfig.model_validate(profile.llm)
        self.artifacts = LiveSessionArtifactDirectoryCreator().create(
            _PROJECT_ROOT,
            self.llm.backend,
            LiveSessionArtifactScope(domain="gate", scenario="mcp-startup"),
        )
        shutil.copy2(profile.profile_path, self.artifacts / "model-profile.toml")
        (self.artifacts / "canonical-audit-path.txt").write_text(str(self.audit))
        print(f"\nStartup artifacts: {self.artifacts}\nCanonical audit: {self.audit}")

    def test_delayed_server_is_available_on_the_first_probe(self):
        server = _PROJECT_ROOT / "mcp-server/flow_engine/server.py"
        result = self._run(
            [
                "-c",
                f"import time, runpy; time.sleep(15); runpy.run_path({str(server)!r}, run_name='__main__')",
            ]
        )

        self.assertEqual(result, "function")
        diagnostics = (self.audit / "codex-execution.log").read_text()
        self.assertIn('"thread.started"', diagnostics)
        self.assertIn('"turn.completed"', diagnostics)

    def test_failed_server_prevents_model_execution(self):
        with self.assertRaises(SubprocessError):
            self._run(["-c", "raise SystemExit('required startup fixture failed')"])

        diagnostics = (self.audit / "codex-execution.log").read_text()
        self.assertIn("solid-coder-flow-engine", diagnostics)
        self.assertNotIn('"agent_message"', diagnostics)
        self.assertNotIn('"turn.completed"', diagnostics)

    def _run(self, server_arguments: list[str]):
        configuration = json.loads(
            McpConfigBuilder(
                _PROJECT_ROOT,
                McpConfigProfile.GATE_FLOW,
                JsonSerializer(),
            ).build()
        )
        configuration["mcpServers"]["solid-coder-flow-engine"]["args"] = (
            server_arguments
        )
        prompt = (
            "Read-only capability probe. Make exactly one tool call, using functions.exec "
            "with JavaScript: text(typeof tools.mcp__solid_coder_flow_engine__flow_next); "
            "Do not invoke flow_next or start a workflow. Do not enumerate tools, search, "
            "read or edit files. Return only the resulting typeof string, without quotes "
            f"or formatting.\nspawned-by: {self.parent_session_id}"
        )
        try:
            with patch.dict(
                os.environ,
                {
                    "SOLID_CODER_SESSION_TYPE": "health_check",
                    "CLAUDE_PROJECT_DIR": str(self.project),
                    "CODEX_WORKSPACE_ROOT": str(self.project),
                },
            ):
                return make_codex_runner(
                    model=self.llm.model,
                    cwd=str(self.project),
                    mcp_config=json.dumps(configuration),
                ).run(prompt, timeout=120)
        finally:
            if self.audit.exists():
                shutil.copytree(self.audit, self.artifacts / "audit")
