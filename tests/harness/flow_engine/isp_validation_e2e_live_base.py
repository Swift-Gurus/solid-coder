"""Defines the backend-neutral live ISP workflow expectations."""

from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURES = _PROJECT_ROOT / "tests/principles/ISP/fixtures/interface-extensions"


"""
solid-name: ISPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-057]
solid-description: Tests the bundled ISP policy on definition-first and aggregate extension-first reviews with locked member, responsibility, and stakeholder expectations.
"""
class ISPValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "isp"
    ARTIFACT_SCENARIO = "isp"
    FIXTURE = _FIXTURES / "CustomerOperations.swift"
    EXPECTED_STEP_IDS = ["width", "responsibilities", "stakeholders"]
    EXPECTED_ANALYSIS_STEP_IDS = ["classify_members"]
    EXPECTED_METRIC_IDS = ["ISP-1", "ISP-3", "ISP-5"]
    EXPECTED_VALUES = [3, 3, 2]
    EXPECTED_METRIC_SEVERITIES = ["COMPLIANT", "SEVERE", "SEVERE"]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True

    def setUp(self) -> None:
        super().setUp()
        self._companion = self._source_project.root / "Sources/CustomerOperations+Tax.swift"
        shutil.copy2(_FIXTURES / "CustomerOperations+Tax.swift", self._companion)

    def test_extension_first_aggregate_workflow(self) -> None:
        self._companion.unlink()
        shutil.copy2(self.FIXTURE, self._source_project.root / "Sources/CustomerOperations.swift")
        self.FIXTURE = _FIXTURES / "CustomerOperations+Tax.swift"
        shutil.copy2(self.FIXTURE, self._source_project.review_target)
        self.REVIEW_WORKFLOW_ID = "isp-aggregate-test"
        self.ARTIFACT_SCENARIO = "isp-extension-aggregate"
        package = self._source_project.root / ".solid-coder/workflows/test/isp-aggregate-test"
        package.mkdir(parents=True)
        (package / "workflow.yaml").write_text(textwrap.dedent("""
            id: isp-aggregate-test
            name: Aggregate real bundled review
            max_turns: 20
            steps:
              - group: reviews
                execution: {mode: aggregate}
                presentation: {mode: combined}
                steps:
                  - include: {workflow: solid-review}
                    as: review
                    with:
                      target: "{{params.target}}"
        """), encoding="utf-8")

        self.assert_workflow(self._run_scenario(self.scenario))

    def assert_workflow(self, run) -> None:
        super().assert_workflow(run)
        events = [json.loads(line) for line in (run.run_directory / "events.jsonl").read_text().splitlines()]
        prepared = [event for event in events
                    if event.get("event") == "step_completed" and event.get("local_step_id") == "prepare_context"]
        self.assertEqual(len(prepared), 1)
        self.assertEqual(prepared[0]["session_id"], "engine")
        self.assertEqual(len(prepared[0]["outputs"]["members"]), 3)
        self.assertNotIn("taxFormattingScratch", prepared[0]["outputs"]["context"])
        self.assertNotIn("taxStorageScratch", prepared[0]["outputs"]["context"])
        classified = [event for event in events
                      if event.get("event") == "step_completed" and event.get("local_step_id") == "classify_members"]
        self.assertEqual(len(classified), 3)
