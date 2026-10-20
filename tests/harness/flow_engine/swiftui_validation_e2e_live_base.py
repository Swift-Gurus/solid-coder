"""Defines the backend-neutral live SwiftUI expectations."""

from __future__ import annotations

import json
from pathlib import Path

from preserved_live_workflow_run import PreservedLiveWorkflowRun
from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = (
    _PROJECT_ROOT
    / "tests"
    / "coding"
    / "apple"
    / "swiftui"
    / "fixtures"
    / "fixture-1.swift"
)


"""
solid-name: SwiftUIValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-055, SPEC-057]
solid-description: Supplies the first SwiftUI review-unit result and locked mixed MCP/model-scored observations to the shared live rule contract.
"""
class SwiftUIValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "swiftui"
    ARTIFACT_SCENARIO = "swiftui-aggregate"
    REVIEW_WORKFLOW_ID = "solid-file-review-aggregate"
    FIXTURE = _FIXTURE
    EXPECTED_ANALYSIS_STEP_IDS = [
        "classify_countable_observations",
        "classify_extrema_observations",
        "classify_view_purity",
    ]
    EXPECTED_STEP_IDS = [
        "body_nesting_depth",
        "view_expression_count",
        "max_modifier_chain",
        "impure_count",
        "vm_injection_style",
        "preview_only_count",
        "views_without_preview_count",
        "bad_accessibility_count",
        "fixed_frame_count",
        "over_isolated_count",
    ]
    EXPECTED_METRIC_IDS = [
        "SUI-1",
        "SUI-2",
        "SUI-3",
        "SUI-4",
        "SUI-5",
        "SUI-6",
        "SUI-7",
        "SUI-8",
        "SUI-9",
        "SUI-10",
    ]
    EXPECTED_VALUES = [2, 8, 2, 2, "concrete", 0, 1, 1, 1, 1]
    EXPECTED_METRIC_SEVERITIES = ["SEVERE"] * 5 + ["COMPLIANT"] + ["SEVERE"] * 4
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    EXPECTED_RULE_SOURCE_INDEX = 1
    EXPECTED_RULE_RESULT_COUNT = 2
    ALLOW_AUXILIARY_STEPS = True

    def assert_workflow(self, run: PreservedLiveWorkflowRun) -> None:
        super().assert_workflow(run)
        events = [
            json.loads(line)
            for line in (run.run_directory / "events.jsonl").read_text().splitlines()
            if line.strip()
        ]
        completed = [
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("workflow_source_index")
            == self.EXPECTED_RULE_SOURCE_INDEX
            and self._belongs_to_rule(event.get("workflow_instance_id"))
        ]
        countable = next(
            event
            for event in completed
            if event.get("local_step_id") == "classify_countable_observations"
        )
        self.assertEqual(countable["outputs"]["preview_limitations"], [])
        preview_facts = countable["outputs"]["preview_facts"]
        self.assertEqual(len(preview_facts), 1)
        self.assertFalse(preview_facts[0]["is_preview"])
        self.assertTrue(preview_facts[0]["is_file_scope"])
        self.assertFalse(preview_facts[0]["has_preview"])
        extrema = next(
            event
            for event in completed
            if event.get("local_step_id") == "classify_extrema_observations"
        )
        for observation in extrema["outputs"]["view_properties"]:
            self.assertNotIn("nesting_depth", observation)
            self.assertNotIn("expression_count", observation)
        for observation in extrema["outputs"]["modifier_chains"]:
            self.assertNotIn("length", observation)
        self.assertEqual(extrema["outputs"]["limitations"], [])
        purity = next(
            event
            for event in completed
            if event.get("local_step_id") == "classify_view_purity"
        )
        self.assertEqual(purity["outputs"]["limitations"], [])
        self.assertIn(
            "ACTION_FORWARDING",
            [behavior["classification"] for behavior in purity["outputs"]["behaviors"]],
        )
        self._assert_ordered_counts(completed, "count_nesting_paths", [2])
        self._assert_ordered_counts(completed, "count_view_expressions", [8])
        self._assert_ordered_counts(
            completed,
            "count_modifier_chains",
            [2, 1, 1],
        )

    def _assert_ordered_counts(
        self,
        completed: list[dict[str, object]],
        step_id: str,
        expected: list[int],
    ) -> None:
        matching = sorted(
            (
                event
                for event in completed
                if event.get("local_step_id") == step_id
            ),
            key=lambda event: event["iteration_index"],
        )
        self.assertEqual(
            [event["outputs"]["value"] for event in matching],
            expected,
        )
