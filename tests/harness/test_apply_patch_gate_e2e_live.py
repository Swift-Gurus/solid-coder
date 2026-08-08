"""
solid-name: test_apply_patch_gate_e2e_live
solid-category: integration-test
solid-description: Verifies a real Codex session fans one multi-file patch into isolated health reviews and returns one atomic denial.

Run explicitly with:
    python3 -m pytest tests/harness/test_apply_patch_gate_e2e_live.py -v -s
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_HARNESS_DIR = Path(__file__).resolve().parent
_MCP_SERVER = _PROJECT_ROOT / "mcp-server"
_MCP_HEALTH_CODEX = _MCP_SERVER / "health" / "codex"
for _directory in (_HARNESS_DIR, _MCP_SERVER, _MCP_HEALTH_CODEX):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness_factory import HookUtilsTomlLoader  # noqa: E402
from hook_utils import solid_coder_project_dir  # noqa: E402
from codex_apply_patch_transcript_reader import (  # noqa: E402
    CodexApplyPatchTranscriptReader,
)
from model_profile_loader import ModelProfileLoader  # noqa: E402

_MODEL_PROFILE = "codex"
_ARTIFACT_ROOT = (
    _PROJECT_ROOT
    / ".solid-coder"
    / ".artifacts"
    / "test"
    / "codex"
    / "e2e"
    / "apply-patch-gate"
)
_VIEW_NAMES = (
    "DashboardView.swift",
    "OrdersView.swift",
    "InventoryView.swift",
    "AnalyticsView.swift",
)
_EXPECTED_PRINCIPLE_OUTPUTS = (
    "code-smells",
    "dry",
    "frontmatter",
    "isp",
    "lsp",
    "ocp",
    "srp",
)


class TestApplyPatchGateE2ELive(unittest.TestCase):
    """Runs the development checkout's real hook through a Codex Terra session."""

    TIMEOUT = 1200

    def setUp(self) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_dir = _ARTIFACT_ROOT / f"{timestamp}-{uuid.uuid4().hex[:8]}"
        self.run_dir.mkdir(parents=True)
        self.generated_config = self.run_dir / "codex-config.toml"
        self.codex_home = Path(tempfile.mkdtemp(prefix="solid-coder-e2e-codex-home-"))
        relative_run_dir = self.run_dir.relative_to(_PROJECT_ROOT)
        self.relative_files = tuple(
            str(relative_run_dir / "workspace" / name)
            for name in _VIEW_NAMES
        )

    def tearDown(self) -> None:
        self.generated_config.unlink(missing_ok=True)
        shutil.rmtree(self.codex_home, ignore_errors=True)

    def test_four_swiftui_files_are_reviewed_isolated_and_denied_atomically(self) -> None:
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(_MODEL_PROFILE)
        project_state = solid_coder_project_dir(_PROJECT_ROOT)
        before_inputs = set(project_state.glob("health-*/hook-input.json"))
        prompt = self._prompt()
        self.generated_config.write_text(self._codex_config(), encoding="utf-8")
        shutil.copyfile(self.generated_config, self.codex_home / "config.toml")
        auth_path = Path.home() / ".codex" / "auth.json"
        self.assertTrue(auth_path.exists(), f"Codex auth file not found: {auth_path}")
        (self.codex_home / "auth.json").symlink_to(auth_path)

        started = time.monotonic()
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(self.codex_home)
        environment["SOLID_CODER_TEST_MODEL_PROFILE"] = str(profile.profile_path)
        try:
            self._install_current_plugin(environment)
            process = subprocess.run(
                self._codex_command(profile.llm["model"]),
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT,
                cwd=str(_PROJECT_ROOT),
                env=environment,
            )
        finally:
            self._preserve_codex_runtime()
            self.generated_config.unlink(missing_ok=True)
            shutil.rmtree(self.codex_home, ignore_errors=True)
        elapsed = time.monotonic() - started

        (self.run_dir / "codex-events.jsonl").write_text(process.stdout, encoding="utf-8")
        (self.run_dir / "codex-stderr.log").write_text(process.stderr, encoding="utf-8")
        after_inputs = set(project_state.glob("health-*/hook-input.json"))
        new_inputs = after_inputs - before_inputs
        health_directories = self._health_directories_by_file(new_inputs)
        reviewed_paths = set(health_directories)
        expected_paths = {
            str((_PROJECT_ROOT / relative_path).resolve())
            for relative_path in self.relative_files
        }
        result_path = self.run_dir / "last-message.txt"
        result_text = result_path.read_text(encoding="utf-8") if result_path.exists() else ""
        self._assert_single_multi_file_apply_patch()
        print(
            f"\n--- apply_patch gate live result ({elapsed:.2f}s) ---\n"
            f"{result_text}\n"
            f"review inputs: {sorted(reviewed_paths)}\n"
            "--- end live result ---\n",
            flush=True,
        )

        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(reviewed_paths, expected_paths)
        self._assert_complete_principle_outputs(health_directories)
        self.assertTrue(result_text, "The outer Codex session returned no final result.")
        self.assertIn("den", result_text.lower(), "The intentionally severe patch was not denied.")
        for relative_path in self.relative_files:
            self.assertIn(Path(relative_path).name, result_text)
            self.assertFalse(
                (_PROJECT_ROOT / relative_path).exists(),
                f"Atomic denial failed: {relative_path} was written.",
            )

    def _prompt(self) -> str:
        paths = ", ".join(self.relative_files)
        return (
            "This is a live pre-write hook integration test. Do not inspect the repository and "
            "do not use shell commands to create files. In exactly one apply_patch tool call, add "
            f"these four files: {paths}. Make every file at least 80 lines. In each SwiftUI View "
            "type intentionally combine rendering, mutable state, filtering, business calculations, "
            "async data loading, navigation decisions, currency/date formatting, status-color "
            "selection, and loading/error presentation. Intentionally duplicate the same private "
            "currency formatter, date formatter, status-color mapping, and loading/error logic in "
            "all four files; this duplication is required test data and must not be extracted. Use "
            "only Swift and SwiftUI. After that one apply_patch returns, do not retry or fix anything. "
            "Report whether the hook allowed or denied the patch, reproduce the complete hook "
            "response including every affected filename, and stop."
        )

    def _codex_config(self) -> str:
        return (
            "[features]\n"
            "plugins = true\n\n"
            "[marketplaces.solid-coder]\n"
            'source_type = "local"\n'
            f"source = {json.dumps(str(_PROJECT_ROOT))}\n\n"
            '[plugins."solid-coder@solid-coder"]\n'
            "enabled = true\n"
        )

    def _codex_command(self, model: str) -> list[str]:
        return [
            "codex",
            "exec",
            "--json",
            "--dangerously-bypass-approvals-and-sandbox",
            "--dangerously-bypass-hook-trust",
            "--skip-git-repo-check",
            "--model",
            model,
            "--output-last-message",
            str(self.run_dir / "last-message.txt"),
            "-",
        ]

    def _install_current_plugin(self, environment: dict[str, str]) -> None:
        process = subprocess.run(
            ["codex", "plugin", "add", "solid-coder@solid-coder", "--json"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(_PROJECT_ROOT),
            env=environment,
        )
        (self.run_dir / "plugin-install.json").write_text(process.stdout, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr)

    def _preserve_codex_runtime(self) -> None:
        runtime_artifacts = self.run_dir / "codex-runtime"
        sessions = self.codex_home / "sessions"
        if sessions.exists():
            shutil.copytree(sessions, runtime_artifacts / "sessions")
        for database in self.codex_home.glob("state_*.sqlite*"):
            runtime_artifacts.mkdir(parents=True, exist_ok=True)
            shutil.copy2(database, runtime_artifacts / database.name)

    def _health_directories_by_file(self, inputs: set[Path]) -> dict[str, Path]:
        expected_names = set(_VIEW_NAMES)
        directories = {}
        for input_path in inputs:
            payload = json.loads(input_path.read_text(encoding="utf-8"))
            file_path = str(Path(payload["file_path"]).resolve())
            if Path(file_path).name in expected_names:
                directories[file_path] = input_path.parent
        return directories

    def _assert_complete_principle_outputs(self, health_directories: dict[str, Path]) -> None:
        for file_path, health_directory in health_directories.items():
            for principle in _EXPECTED_PRINCIPLE_OUTPUTS:
                output = health_directory / principle / "review-output.json"
                self.assertTrue(output.exists(), f"{file_path} missing {principle} output")
                json.loads(output.read_text(encoding="utf-8"))

    def _assert_single_multi_file_apply_patch(self) -> None:
        sessions_root = self.run_dir / "codex-runtime" / "sessions"
        calls = CodexApplyPatchTranscriptReader().read(sessions_root)
        transcript_paths = [str(call.transcript_path) for call in calls]
        self.assertEqual(
            len(calls),
            1,
            f"Expected exactly one apply_patch invocation; observed {transcript_paths}",
        )
        added_files = [
            line.removeprefix("*** Add File: ")
            for line in calls[0].patch_content.splitlines()
            if line.startswith("*** Add File: ")
        ]
        self.assertEqual(added_files, list(self.relative_files))


if __name__ == "__main__":
    unittest.main()
