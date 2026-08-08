"""
solid-name: test_srp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-034]
solid-description: Verifies the project SRP validation flow resolves by bare name, measures three independent metrics with supporting evidence, interpolates recorded values, rejects malformed output, and completes with a scorer response.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.static_session_id_reader import StaticSessionIdReader  # noqa: E402

_PARAMS = {
    "code": "final class Example {\n    func load() {}\n    func save() {}\n}",
    "file_path": "/tmp/Example.swift",
    "unit_name": "Example",
    "unit_kind": "class",
    "timestamp": "2026-08-02T20:00:00Z",
}
_MEASUREMENTS = {
    "measure_verbs": {
        "verb_count": 2,
        "verb_evidence": [
            {"method": "load", "action": "load", "rationale": "Loads data."},
            {"method": "save", "action": "save", "rationale": "Saves data."},
        ],
    },
    "measure_cohesion": {
        "cohesion_groups": 1,
        "cohesion_evidence": [
            {"methods": ["load", "save"], "variables": ["storage"], "rationale": "Shared storage."},
        ],
    },
    "measure_stakeholders": {
        "stakeholder_count": 1,
        "stakeholder_evidence": [
            {"stakeholder": "data", "methods": ["load", "save"], "rationale": "Data access."},
        ],
    },
}


class TestSRPValidationFlow(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        runs_root = Path(temporary.name)
        (runs_root / "runs").mkdir()
        environment = patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(_PROJECT_ROOT)})
        environment.start()
        self.addCleanup(environment.stop)
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(project_dir_fn=lambda: runs_root),
            plugin_root=_PROJECT_ROOT,
            session_reader=StaticSessionIdReader("spec-034-test"),
        ).build()
        self.runs_dir = runs_root / "runs"

    def _start(self):
        return self.sut.flow_start("srp_validation", _PARAMS)

    def _submit_measurements(self, start_result):
        outputs = {
            step.instance_id: _MEASUREMENTS[step.step_id]
            for step in start_result.steps
        }
        return self.sut.flow_next(outputs)

    def test_bare_name_start_returns_three_independent_metric_steps(self):
        result = self._start()

        self.assertEqual(
            {step.step_id for step in result.steps},
            {"measure_verbs", "measure_cohesion", "measure_stakeholders"},
        )

    def test_each_metric_prompt_contains_the_exact_supplied_source(self):
        result = self._start()

        self.assertTrue(all(_PARAMS["code"] in step.prompt for step in result.steps))

    def test_non_integer_metric_is_rejected_without_making_scoring_ready(self):
        start = self._start()
        verb_step = next(step for step in start.steps if step.step_id == "measure_verbs")

        result = self.sut.flow_next({verb_step.instance_id: {"verb_count": "two"}})

        self.assertEqual(result.status, "ready")
        self.assertNotIn("score_results", {step.step_id for step in result.steps})
        rejected = next(step for step in result.steps if step.step_id == "measure_verbs")
        self.assertIn("not of type 'integer'", rejected.rejection_reason)

    def test_all_measurements_make_scoring_ready_with_recorded_values_and_metadata(self):
        start = self._start()

        result = self._submit_measurements(start)

        self.assertEqual([step.step_id for step in result.steps], ["score_results"])
        prompt = result.steps[0].prompt
        for expected in ("value: 2", "value: 1", _PARAMS["file_path"], _PARAMS["unit_name"], _PARAMS["timestamp"]):
            self.assertIn(expected, prompt)

    def test_malformed_scorer_response_is_rejected_and_scoring_remains_ready(self):
        scoring = self._submit_measurements(self._start())

        result = self.sut.flow_next({scoring.steps[0].instance_id: {"scored_review": {"error": "bad"}}})

        self.assertEqual(result.status, "ready")
        self.assertEqual([step.step_id for step in result.steps], ["score_results"])
        self.assertIn("'results' is a required property", result.steps[0].rejection_reason)

    def test_valid_scorer_response_completes_and_records_all_outputs(self):
        start = self._start()
        scoring = self._submit_measurements(start)
        scored_review = {"results": [{"files": [{"units": [{"violations": []}]}]}]}

        result = self.sut.flow_next({scoring.steps[0].instance_id: {"scored_review": scored_review}})

        self.assertEqual(result.status, "done")
        events_path = self.runs_dir / start.run_id / "events.jsonl"
        events = [json.loads(line) for line in events_path.read_text().splitlines()]
        completed = [event for event in events if event["event"] == "step_completed"]
        self.assertEqual(len(completed), 4)


if __name__ == "__main__":
    unittest.main()
