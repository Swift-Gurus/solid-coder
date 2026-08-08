"""
solid-name: test_srp_validation_live
solid-category: integration-test
solid-spec: [SPEC-034]
solid-description: Drives the project SRP validation flow through a real Codex Terra session and verifies every recorded metric, its supporting evidence, and the deterministic findings exactly match the paired SRP fixture expectation.

Run explicitly with: python3 tests/harness/flow_engine/test_srp_validation_live.py
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER = _PROJECT_ROOT / "mcp-server"
_MCP_HEALTH_CODEX = _MCP_SERVER / "health" / "codex"
for _directory in (_MCP_SERVER, _MCP_HEALTH_CODEX):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from hook_utils import solid_coder_project_dir  # noqa: E402
from hc_codex_runner import make_codex_runner  # noqa: E402

_FLOW = _PROJECT_ROOT / ".solid-coder" / "harness" / "flows" / "srp_validation.yaml"
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "SRP" / "fixtures" / "fixture-1.swift"
_EXPECTATION = _PROJECT_ROOT / "tests" / "principles" / "SRP" / "expectations" / "fixture-1.json"
_UNIT_NAME = "ProductCatalog"
_MODEL = "gpt-5.6-terra"
_EXPECTED_STEP_OUTPUTS = {
    "measure_verbs": ("verb_count", "verb_evidence", 6),
    "measure_cohesion": ("cohesion_groups", "cohesion_evidence", 2),
    "measure_stakeholders": ("stakeholder_count", "stakeholder_evidence", 2),
}


class TestSRPValidationLive(unittest.TestCase):

    TIMEOUT = 1000

    def setUp(self):
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        if runs_dir.exists():
            for pointer in runs_dir.glob("active*.json"):
                pointer.unlink(missing_ok=True)

    def test_fixture_completes_every_step_with_expected_outputs_and_exact_findings(self):
        runs_dir = solid_coder_project_dir(_PROJECT_ROOT) / "runs"
        before = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        source = _FIXTURE.read_text(encoding="utf-8")
        params = {
            "code": source,
            "file_path": str(_FIXTURE),
            "unit_name": _UNIT_NAME,
            "unit_kind": "class",
            "timestamp": "2026-08-02T20:00:00Z",
        }
        prompt = (
            f"Call flow_start with flow={json.dumps(str(_FLOW))} and params equal to this JSON. "
            "Drive every returned step with flow_next until the flow reaches done. Do not edit files: "
            f"{json.dumps(params)}"
        )
        runner = make_codex_runner(model=_MODEL, cwd=str(_PROJECT_ROOT))

        result_message = runner.run(prompt, timeout=self.TIMEOUT)

        after = set(runs_dir.glob("*/events.jsonl")) if runs_dir.exists() else set()
        new_logs = after - before
        self.assertTrue(new_logs, f"No flow event log was created. Codex output: {result_message}")
        events_path = max(new_logs, key=lambda path: path.stat().st_mtime)
        events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
        completed_steps = [event for event in events if event.get("event") == "step_completed"]
        metric_steps = completed_steps[:-1]
        score_event = completed_steps[-1]

        self.assertEqual(events[-1]["event"], "run_completed", f"Codex output: {result_message}")
        self.assertFalse(
            {event.get("event") for event in events} & {"step_attempt_failed", "step_rejected", "run_failed"}
        )
        self.assertEqual({event["step_id"] for event in metric_steps}, set(_EXPECTED_STEP_OUTPUTS))
        self.assertEqual(score_event["step_id"], "score_results")
        metric_outputs = {event["step_id"]: event["outputs"] for event in metric_steps}
        for step_id, (metric_name, evidence_name, expected_value) in _EXPECTED_STEP_OUTPUTS.items():
            outputs = metric_outputs[step_id]
            self.assertEqual(outputs[metric_name], expected_value)
            self.assertEqual(len(outputs[evidence_name]), expected_value)
        recorded_sessions = [event for event in events if event.get("event") == "session_step_recorded"]
        self.assertEqual(
            {event["instance_id"] for event in recorded_sessions},
            {"measure_verbs-1", "measure_cohesion-1", "measure_stakeholders-1", "score_results-1"},
        )

        scored_review = score_event["outputs"]["scored_review"]
        scored_unit = scored_review["results"][0]["files"][0]["units"][0]
        scored_metrics = {
            name: value["value"]
            for name, value in scored_unit["metrics"]["SRP"].items()
        }
        self.assertEqual(
            scored_metrics,
            {"verb_count": 6, "cohesion_groups": 2, "stakeholder_count": 2},
        )

        actual_findings = {
            (scored_unit["unit_name"], violation["rule_id"], violation["severity"])
            for violation in scored_unit["violations"]
        }
        expected_entries = json.loads(_EXPECTATION.read_text(encoding="utf-8"))["findings"]
        expected_findings = {
            (entry["unit_name"], entry["metric_id"], entry["severity"])
            for entry in expected_entries
        }
        self.assertEqual(actual_findings, expected_findings)
        for entry in expected_entries:
            for metric_name, expected_value in entry.get("metrics", {}).items():
                self.assertEqual(scored_metrics[metric_name], expected_value)


if __name__ == "__main__":
    unittest.main()
