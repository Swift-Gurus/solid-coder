"""Checks the bundled LSP relationship path with both locked model profiles."""

import sys
from pathlib import Path
from typing import ClassVar

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "tests/harness"))

from claude_test_base import ClaudeTestBase
from codex_test_base import CodexTestBase
from harness.event_replayer import EventParser
from harness.step_completed_event import StepCompletedEvent
from lsp_validation_e2e_live_base import LSPValidationE2ELiveBase

"""
solid-name: LSPRepositoryRelationshipLiveBase
solid-category: test-support
solid-spec: [SPEC-057, SPEC-064]
solid-description: Reuses the real bundled-rule live contract to verify one contract comparison after candidate reading, without a duplicate child classification.
"""


class LSPRepositoryRelationshipLiveBase(LSPValidationE2ELiveBase):
    __test__ = False
    FIXTURE = ROOT / "tests/principles/LSP/fixtures/fixture-3.swift"
    ARTIFACT_SCENARIO = "lsp-relationships"
    EXPECTED_STEP_IDS: ClassVar[list[str]] = [
        "type_checks",
        "contract_violations",
        "fatal_error_methods",
        "fatal_calls",
        "empty_methods",
    ]
    EXPECTED_METRIC_IDS: ClassVar[list[str]] = [
        "LSP-1",
        "LSP-2",
        "LSP-3",
        "LSP-3",
        "LSP-4",
    ]
    EXPECTED_OBSERVATION_IDS: ClassVar[list[str]] = [
        "value",
        "value",
        "value",
        "fatal_calls",
        "value",
    ]
    EXPECTED_VALUES: ClassVar[list[int]] = [0, 1, 0, 0, 0]
    EXPECTED_METRIC_SEVERITIES: ClassVar[list[str]] = [
        "COMPLIANT",
        "SEVERE",
        "COMPLIANT",
        "COMPLIANT",
        "COMPLIANT",
    ]
    EXPECTED_UNAVAILABLE_METRIC_IDS: ClassVar[list[str]] = []
    EXPECTED_ANALYSIS_STEP_IDS: ClassVar[list[str]] = [
        "analyze_substitutability",
        "select_relationship_candidates",
        "classify_relationship_violations",
    ]

    def assert_workflow(self, run):
        super().assert_workflow(run)
        events = EventParser().parse(
            (run.run_directory / "events.jsonl").read_text().splitlines()
        )
        completed = [
            StepCompletedEvent.model_validate(event)
            for event in events
            if event.get("event") == "step_completed"
        ]
        readings = [
            event for event in completed if event.local_step_id == "inspect_candidate"
        ]
        self.assertEqual(len(readings), 1)
        self.assertTrue(readings[0].outputs["evidence"])
        self.assertFalse(
            any(event.local_step_id == "classify_relationship" for event in completed)
        )
        judgments = [
            event
            for event in completed
            if event.local_step_id == "classify_relationship_violations"
            and event.workflow_source_index == self.EXPECTED_RULE_SOURCE_INDEX
        ]
        self.assertEqual(len(judgments), 1)
        self.assertLess(completed.index(readings[0]), completed.index(judgments[0]))
        self.assertEqual(
            [entry["classification"] for entry in judgments[0].outputs["observations"]],
            ["NEW_GUARD"],
        )
        print(f"LSP relationship evidence: {run.run_directory}")


class TestCodexLSPRepositoryRelationshipLive(
    CodexTestBase, LSPRepositoryRelationshipLiveBase
):
    __test__ = True


class TestClaudeLSPRepositoryRelationshipLive(
    ClaudeTestBase, LSPRepositoryRelationshipLiveBase
):
    __test__ = True
