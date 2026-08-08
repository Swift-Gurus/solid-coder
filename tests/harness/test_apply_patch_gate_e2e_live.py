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
from codex_apply_patch_transcript_reader import (  # noqa: E402
    CodexApplyPatchTranscriptReader,
)
from codex_health_review_transcript_reader import (  # noqa: E402
    CodexHealthReviewTranscriptReader,
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
        result_path = self.run_dir / "last-message.txt"
        result_text = result_path.read_text(encoding="utf-8") if result_path.exists() else ""
        self._assert_single_multi_file_apply_patch()
        reviewed_file_names = self._assert_isolated_health_reviews()
        print(
            f"\n--- apply_patch gate live result ({elapsed:.2f}s) ---\n"
            f"{result_text}\n"
            f"reviewed files: {reviewed_file_names}\n"
            "--- end live result ---\n",
            flush=True,
        )

        self.assertEqual(process.returncode, 0, process.stderr)
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

    def _assert_single_multi_file_apply_patch(self) -> None:
        sessions_root = self.run_dir / "codex-runtime" / "sessions"
        calls = CodexApplyPatchTranscriptReader().read(sessions_root)
        transcript_paths = [str(call.transcript_path) for call in calls]
        self.assertEqual(
            len(calls),
            1,
            f"Expected exactly one apply_patch invocation; observed {transcript_paths}",
        )
        file_operations = [
            line
            for line in calls[0].patch_content.splitlines()
            if line.startswith(
                (
                    "*** Add File: ",
                    "*** Update File: ",
                    "*** Delete File: ",
                    "*** Move to: ",
                )
            )
        ]
        expected_operations = [
            f"*** Add File: {relative_file}"
            for relative_file in self.relative_files
        ]
        self.assertEqual(file_operations, expected_operations)

    def _assert_isolated_health_reviews(self) -> list[str]:
        sessions_root = self.run_dir / "codex-runtime" / "sessions"
        submissions = CodexHealthReviewTranscriptReader().read(sessions_root)
        transcript_paths = frozenset(
            submission.transcript_path for submission in submissions
        )
        self.assertEqual(
            len(transcript_paths),
            len(_VIEW_NAMES),
            "Expected one isolated health-review transcript per edited file",
        )
        successful_submissions = []
        for transcript_path in transcript_paths:
            attempts = [
                submission
                for submission in submissions
                if submission.transcript_path == transcript_path
            ]
            successful_attempts = [
                submission for submission in attempts if submission.successful
            ]
            self.assertEqual(
                len(successful_attempts),
                1,
                f"Expected one successful submission in {transcript_path}",
            )
            self.assertTrue(
                attempts[-1].successful,
                f"Final health-review attempt failed in {transcript_path}",
            )
            successful_submissions.extend(successful_attempts)
        reviewed_file_names = sorted(
            submission.file_name for submission in successful_submissions
        )
        self.assertEqual(reviewed_file_names, sorted(_VIEW_NAMES))
        expected_principles = frozenset(_EXPECTED_PRINCIPLE_OUTPUTS)
        for submission in successful_submissions:
            missing_principles = expected_principles - submission.principle_names
            self.assertFalse(
                missing_principles,
                f"{submission.file_name} missing {sorted(missing_principles)}",
            )
        return reviewed_file_names


if __name__ == "__main__":
    unittest.main()
