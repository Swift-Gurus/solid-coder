"""Defines the Codex live smoke contract for the legacy health checker."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import ClassVar

_HARNESS = Path(__file__).resolve().parent
_PROJECT_ROOT = _HARNESS.parents[1]
_MCP_SERVER = _PROJECT_ROOT / "mcp-server"
_MCP_HEALTH = _MCP_SERVER / "health"
for _directory in (_HARNESS, _MCP_SERVER, _MCP_HEALTH):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness_factory import HookUtilsTomlLoader  # noqa: E402
import code_health_check  # noqa: E402
from codex_health_review_transcript_reader import (  # noqa: E402
    CodexHealthReviewTranscriptReader,
)
from codex_review_stage_evidence_reader import (  # noqa: E402
    CodexReviewStageEvidenceReader,
)
from codex_transcript_token_usage_reader import (  # noqa: E402
    CodexTranscriptTokenUsageReader,
)
from hook_utils import solid_coder_project_dir  # noqa: E402
from live_session_artifact_directory_creator import (  # noqa: E402
    LiveSessionArtifactDirectoryCreator,
)
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_test_base import LiveTestBase  # noqa: E402
from model_profile_environment import model_profile_environment  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402
from review_comparison_run_evidence import (  # noqa: E402
    ReviewComparisonRunEvidence,
)
from review_comparison_stage_evidence import (  # noqa: E402
    ReviewComparisonStageEvidence,
)
from review_comparison_source_project import (  # noqa: E402
    ReviewComparisonSourceProject,
)


"""
solid-name: LegacyHealthComparisonE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Executes and audits the fixed legacy health-review smoke scenario used before repeated comparison.
"""
class LegacyHealthComparisonE2ELiveBase(unittest.TestCase, LiveTestBase):
    __test__ = False

    MODEL_PROFILE: ClassVar[str] = "codex"
    EXPECTED_RULE_IDS: ClassVar[list[str]] = [
        "code-smells",
        "dry",
        "frontmatter",
        "isp",
        "lsp",
        "ocp",
        "srp",
    ]

    def test_legacy_health_satisfies_its_live_contract(self) -> None:
        source_project = ReviewComparisonSourceProject.create()
        self.addCleanup(source_project.cleanup)
        artifact_directory = LiveSessionArtifactDirectoryCreator().create(
            _PROJECT_ROOT,
            "codex",
            LiveSessionArtifactScope(
                domain="comparison",
                scenario="legacy-smoke",
            ),
        )
        profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        health_root = solid_coder_project_dir(source_project.root)
        before = set(health_root.glob("health-*"))
        temporary = tempfile.TemporaryDirectory(
            prefix="solid-coder-legacy-comparison-codex-home-"
        )
        codex_home = Path(temporary.name)
        previous_codex_home = os.environ.get("CODEX_HOME")
        previous_project_directory = os.environ.get("CLAUDE_PROJECT_DIR")
        try:
            self._link_auth(codex_home)
            os.environ["CODEX_HOME"] = str(codex_home)
            os.environ["CLAUDE_PROJECT_DIR"] = str(source_project.root)
            started = time.monotonic()
            with model_profile_environment(profile.profile_path):
                violations = code_health_check._check(
                    source_project.review_target.read_text(encoding="utf-8"),
                    str(source_project.review_target),
                    "Swift",
                    self.parent_session_id,
                    cwd=str(source_project.root),
                )
            elapsed_seconds = time.monotonic() - started
            self._preserve_runtime(codex_home, artifact_directory)
        finally:
            if previous_codex_home is None:
                os.environ.pop("CODEX_HOME", None)
            else:
                os.environ["CODEX_HOME"] = previous_codex_home
            if previous_project_directory is None:
                os.environ.pop("CLAUDE_PROJECT_DIR", None)
            else:
                os.environ["CLAUDE_PROJECT_DIR"] = previous_project_directory
            temporary.cleanup()

        after = set(health_root.glob("health-*"))
        new_health_directories = after - before
        self.assertEqual(len(new_health_directories), 1)
        health_directory = next(iter(new_health_directories))
        preserved_health = artifact_directory / "health-output"
        shutil.copytree(health_directory, preserved_health)
        (artifact_directory / "legacy-violations.json").write_text(
            json.dumps(violations or [], indent=2),
            encoding="utf-8",
        )

        submissions = CodexHealthReviewTranscriptReader().read(
            artifact_directory / "codex-runtime" / "sessions"
        )
        self.assertTrue(submissions)
        self.assertTrue(submissions[-1].successful)
        active_rule_ids = sorted(
            principle.casefold()
            for principle in submissions[-1].principle_names
        )
        self.assertEqual(active_rule_ids, self.EXPECTED_RULE_IDS)
        transcript = submissions[-1].transcript_path
        usage = CodexTranscriptTokenUsageReader().read(transcript)
        self.assertTrue(usage.available)
        review_stage = CodexReviewStageEvidenceReader().read(
            transcript=transcript,
            prompt_marker="You are a SOLID code quality gate",
            completion_tool="submit_batch_findings",
        )
        evidence = ReviewComparisonRunEvidence(
            approach="legacy-health",
            phase="smoke",
            iteration=0,
            model_profile=self.MODEL_PROFILE,
            model=profile.llm["model"],
            target_path=str(source_project.review_target),
            target_sha256=self._sha256(source_project.review_target),
            effective_instructions_sha256=self._instruction_hash(transcript),
            active_rule_ids=active_rule_ids,
            review_stage=review_stage,
            full_run=ReviewComparisonStageEvidence(
                elapsed_seconds=elapsed_seconds,
                token_usage=usage,
            ),
            reported_cost_available=False,
            reported_cost_usd=0,
            retry_count=max(0, len(submissions) - 1),
            error_count=sum(not submission.successful for submission in submissions),
            completed=True,
        )
        (artifact_directory / "comparison-evidence.json").write_text(
            evidence.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _link_auth(codex_home: Path) -> None:
        auth = Path.home() / ".codex" / "auth.json"
        if not auth.exists():
            raise RuntimeError(f"Codex auth file not found: {auth}")
        (codex_home / "auth.json").symlink_to(auth)

    @staticmethod
    def _preserve_runtime(codex_home: Path, artifact_directory: Path) -> None:
        runtime = artifact_directory / "codex-runtime"
        sessions = codex_home / "sessions"
        if sessions.exists():
            shutil.copytree(sessions, runtime / "sessions")
        for database in codex_home.glob("state_*.sqlite*"):
            runtime.mkdir(parents=True, exist_ok=True)
            shutil.copy2(database, runtime / database.name)

    @staticmethod
    def _instruction_hash(transcript: Path) -> str:
        for line in transcript.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            payload = event.get("payload", {})
            if (
                event.get("type") != "response_item"
                or payload.get("type") != "message"
                or payload.get("role") != "user"
            ):
                continue
            for item in payload.get("content", []):
                prompt = item.get("text", "")
                if "You are a SOLID code quality gate" in prompt:
                    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        raise RuntimeError("Legacy health transcript contains no review prompt")

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
