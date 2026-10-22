"""Exercises the real pre-write hook with a configured live health-check model."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path
from typing import ClassVar

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_HARNESS = Path(__file__).resolve().parents[1]
for _directory in (_HARNESS, _PROJECT_ROOT / "mcp-server"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness.review_result import ReviewResult  # noqa: E402
from harness.rule_review_result import RuleReviewResult  # noqa: E402
from harness_factory import HookUtilsTomlLoader  # noqa: E402
from hook_permission_evidence import HookPermissionEvidence  # noqa: E402
from hook_utils import solid_coder_project_dir  # noqa: E402
from live_gate_event import LiveGateEvent  # noqa: E402
from live_session_artifact_directory_creator import (  # noqa: E402
    LiveSessionArtifactDirectoryCreator,
)
from live_session_artifact_scope import LiveSessionArtifactScope  # noqa: E402
from live_test_base import LiveTestBase  # noqa: E402
from llm_config import LlmConfig  # noqa: E402
from model_profile_loader import ModelProfileLoader  # noqa: E402
from review.normalized_review_input import NormalizedReviewInput  # noqa: E402
from review_comparison_source_project import ReviewComparisonSourceProject  # noqa: E402
from source.analysis.provenance.resolved_type_inspections import ResolvedTypeInspections  # noqa: E402


"""
solid-name: SolidGateOnWriteE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-036, SPEC-050]
solid-description: Verifies that the real write hook reviews an absent destination through the bundled aggregate workflow, persists complete scored results, and denies known violations using the selected live model profile.
"""
class SolidGateOnWriteE2ELiveBase(LiveTestBase, unittest.TestCase):
    __test__ = False
    MODEL_PROFILE: ClassVar[str]
    SUBMISSION_FORMAT: ClassVar[str] = "nested"

    def setUp(self) -> None:
        self.project = ReviewComparisonSourceProject.create()
        self.addCleanup(self.project.cleanup)
        self.content = self.project.review_target.read_text(encoding="utf-8")
        self.project.review_target.unlink()
        configuration = self.project.root / ".solid-coder" / "config.toml"
        configuration.parent.mkdir()
        configuration.write_text(
            'code_review_on_write_enabled = true\n'
            '[feature_flags]\nhealth_check_mode = "workflow"\n'
            f'flow_submission_format = "{self.SUBMISSION_FORMAT}"\n',
            encoding="utf-8",
        )
        self.profile = ModelProfileLoader(
            project_root=_PROJECT_ROOT,
            toml_loader=HookUtilsTomlLoader(),
        ).load(self.MODEL_PROFILE)
        self.llm = LlmConfig.model_validate(self.profile.llm)
        if self.llm.backend == "claude":
            self.assertTrue(
                os.environ.get("ANTHROPIC_API_KEY"),
                "The real Claude write gate requires ANTHROPIC_API_KEY; "
                "otherwise its availability guard bypasses review.",
            )
        self.audit = solid_coder_project_dir(self.project.root)
        self.artifacts = LiveSessionArtifactDirectoryCreator().create(
            _PROJECT_ROOT,
            self.llm.backend,
            LiveSessionArtifactScope(domain="gate", scenario="solid-gate-on-write"),
        )
        shutil.copytree(self.project.root, self.artifacts / "input-project")
        (self.artifacts / "prospective-source.swift").write_text(
            self.content, encoding="utf-8",
        )
        shutil.copy2(self.profile.profile_path, self.artifacts / "model-profile.toml")
        (self.artifacts / "canonical-audit-path.txt").write_text(
            str(self.audit), encoding="utf-8",
        )
        print(f"\nGate artifacts: {self.artifacts}\nCanonical audit: {self.audit}")

    def test_hook_completes_aggregate_review_and_denies_severe_buffer(self) -> None:
        self.assertFalse(self.project.review_target.exists())
        self.assertFalse(self.audit.exists(), "Each test must own a fresh audit scope")
        payload = json.dumps({
            "session_id": self.parent_session_id,
            "hook_event_name": "PreToolUse",
            "cwd": str(self.project.root),
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(self.project.review_target),
                "content": self.content,
            },
        })
        (self.artifacts / "hook-input.json").write_text(payload, encoding="utf-8")
        environment = os.environ.copy()
        environment["CLAUDE_PROJECT_DIR"] = str(self.project.root)
        environment["CODEX_WORKSPACE_ROOT"] = str(self.project.root)
        environment["SOLID_CODER_TEST_MODEL_PROFILE"] = str(self.profile.profile_path)
        with (
            (self.artifacts / "hook-stdout.json").open("w") as stdout,
            (self.artifacts / "hook-stderr.log").open("w") as stderr,
        ):
            started_at = time.perf_counter()
            try:
                completed = subprocess.run(
                    [sys.executable, str(_PROJECT_ROOT / "mcp-server/hooks/pre_write_gate.py")],
                    input=payload,
                    text=True,
                    cwd=self.project.root,
                    env=environment,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=self.llm.timeout + 120,
                    check=False,
                )
            finally:
                (self.artifacts / "hook-elapsed-seconds.txt").write_text(
                    str(time.perf_counter() - started_at), encoding="utf-8",
                )
                if self.audit.exists():
                    shutil.copytree(self.audit, self.artifacts / "audit")

        self.assertEqual(completed.returncode, 0, f"Inspect {self.artifacts}")
        response = HookPermissionEvidence.model_validate_json(
            (self.artifacts / "hook-stdout.json").read_text(),
        )
        self.assertEqual(response.decision, "deny", response.reason)
        self.assertNotIn("Gate subprocess failed", response.reason, response.reason)
        self.assertIn("SEVERE violation(s) found", response.reason, response.reason)
        self.assertFalse(self.project.review_target.exists())
        self.assertFalse((self.project.root / "runs").exists())

        gate_log = (self.audit / "gate.log").read_text()
        self.assertIn(
            f"health_check_mode=workflow backend={self.llm.backend} model={self.llm.model}",
            gate_log,
        )
        self.assertNotIn("health_check_mode=legacy", gate_log)
        self.assertIn(f"source_sha256={hashlib.sha256(self.content.encode()).hexdigest()}", gate_log)
        self.assertIn("gate_review_outcome run_id=", gate_log)
        event_paths = list((self.audit / "runs" / "subagents").glob("*/events.jsonl"))
        self.assertEqual(len(event_paths), 1, f"Unexpected gate runs: {event_paths}")
        events_path = event_paths[0]
        metadata = json.loads((events_path.parent / "run-metadata.json").read_text())
        self.assertEqual(metadata["submission_format"], self.SUBMISSION_FORMAT)
        if self.SUBMISSION_FORMAT == "flat_array":
            self.assertTrue(metadata["submission_targets"])
        self.assertEqual(
            events_path.read_bytes(),
            (self.artifacts / "audit" / events_path.relative_to(self.audit)).read_bytes(),
        )
        events = [
            LiveGateEvent.model_validate_json(line)
            for line in events_path.read_text().splitlines() if line.strip()
        ]
        self._assert_execution(events)
        self._assert_results(events_path.parent, response.reason)

    def _assert_execution(self, events: list[LiveGateEvent]) -> None:
        self.assertEqual(events[-1].event, "run_completed")
        self.assertNotIn("run_failed", {event.event for event in events})
        prepared = [
            event for event in events
            if event.event == "step_completed" and event.local_step_id == "prepare_review"
        ]
        self.assertEqual(len(prepared), 1)
        self.assertEqual(prepared[0].session_id, "engine")
        normalized = NormalizedReviewInput.model_validate(prepared[0].outputs)
        self.assertEqual(normalized.review_file.target.code, self.content)
        self.assertEqual(
            [unit.target.name for unit in normalized.units],
            ["CatalogServing", "ReviewComparisonCatalog"],
        )
        self.assertEqual(
            normalized.source_context.sources[0].path.resolve(),
            self.project.review_target.resolve(),
        )
        child_sessions = {
            event.session_id for event in events
            if event.event == "session_step_recorded" and event.session_id != "engine"
        }
        self.assertEqual(len(child_sessions), 1)
        self.assertNotIn(self.parent_session_id, child_sessions)
        self.assertNotIn("", child_sessions)
        submitted_this_turn = 0
        largest_submission = 0
        for event in events:
            if event.event == "turn_counted":
                submitted_this_turn = 0
            if event.event == "step_completed" and event.session_id in child_sessions:
                submitted_this_turn += 1
                largest_submission = max(largest_submission, submitted_this_turn)
        self.assertGreater(largest_submission, 1, "No combined model submission was accepted")
        inspected = [
            ResolvedTypeInspections.model_validate(event.outputs)
            for event in events
            if event.event == "step_completed" and event.local_step_id == "prepare_type_inspections"
        ]
        self.assertTrue(inspected, "The gate did not run semantic type-inspection preparation")
        for prepared_inspections in inspected:
            self.assertEqual(prepared_inspections.limitations, [])
        cache_calls = [
            inspection for prepared_inspections in inspected
            for inspection in prepared_inspections.inspections
            if inspection.inspection.operand == "cache.object(forKey: key as NSString)"
        ]
        self.assertEqual(len(cache_calls), 1)
        self.assertTrue(cache_calls[0].verified)
        self.assertEqual(cache_calls[0].contract.ownership, "external")
        self.assertNotEqual(cache_calls[0].value.resolution.symbol_id, cache_calls[0].contract.resolution.symbol_id)

    def _assert_results(self, run_directory: Path, denial: str) -> None:
        review_directory = run_directory / "results" / "review"
        result = ReviewResult.model_validate_json((review_directory / "result.json").read_text())
        self.assertEqual(result.workflow_id, "solid-gate-on-write")
        self.assertEqual(result.severity, "SEVERE")
        self.assertEqual(
            {rule.workflow_id for rule in result.rule_results},
            {"code-smells", "frontmatter", "srp", "ocp", "lsp", "isp", "dry"},
        )
        self.assertEqual(
            len({rule.rule_instance_id for rule in result.rule_results}),
            len(result.rule_results),
        )
        for rule in result.rule_results:
            persisted = review_directory / rule.workflow_id / rule.rule_instance_id / "result.json"
            self.assertEqual(RuleReviewResult.model_validate_json(persisted.read_text()), rule)
            self.assertEqual(rule.scoring_authority, "mcp")
        fatal_metrics = [
            metric for rule in result.rule_results
            if rule.workflow_id == "lsp" and rule.provenance.source_index == 1
            for metric in rule.metrics
            if metric.metric_id == "LSP-3" and metric.observation_id == "fatal_calls"
        ]
        self.assertEqual(len(fatal_metrics), 1)
        self.assertEqual(fatal_metrics[0].value, 1)
        self.assertEqual(fatal_metrics[0].severity, "SEVERE")
        self.assertIn("LSP-3", denial)
        lsp_results = [
            rule for rule in result.rule_results
            if rule.workflow_id == "lsp" and rule.provenance.source_index == 1
        ]
        self.assertEqual(len(lsp_results), 1)
        self.assertNotIn("LSP-1", [metric.metric_id for metric in lsp_results[0].unavailable_metrics])
        type_check_metrics = [metric for metric in lsp_results[0].metrics if metric.metric_id == "LSP-1"]
        self.assertEqual(len(type_check_metrics), 1)
        self.assertEqual(type_check_metrics[0].observation_id, "value")
        code_smells = next(rule for rule in result.rule_results if rule.workflow_id == "code-smells")
        boundary = next(metric for metric in code_smells.metrics if metric.metric_id == "CS-2")
        self.assertEqual(boundary.value, 1, "The contract and its implementation form one boundary")
        self.assertEqual(boundary.severity, "COMPLIANT")
        class_dry = next(
            rule for rule in result.rule_results
            if rule.workflow_id == "dry" and rule.provenance.source_index == 1
        )
        self.assertCountEqual(
            [metric.metric_id for metric in class_dry.metrics],
            ["DRY-1", "DRY-2", "DRY-2"],
        )
