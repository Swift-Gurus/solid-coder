"""
solid-name: test_srp_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies packaged SRP observation, validation, scoring, and audit behavior through the flow engine.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestSRPValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="srp",
        rule_path=_PROJECT_ROOT / "references" / "principles" / "SRP" / "rule.md",
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "SRP"
            / "fixtures"
            / "fixture-1.swift"
        ),
        metrics=[
            RuleMetricExpectation(
                step_id="verb_count",
                metric_id="SRP-1",
                detection_id="SRP-1",
                detection_name="Verb Count",
                value=6,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="cohesion_groups",
                metric_id="SRP-2",
                detection_id="SRP-2",
                detection_name="Cohesion Groups",
                value=2,
                severity="SEVERE",
            ),
            RuleMetricExpectation(
                step_id="stakeholder_count",
                metric_id="SRP-3",
                detection_id="SRP-3",
                detection_name="Stakeholder Count",
                value=2,
                severity="SEVERE",
            ),
        ],
        final_severity="SEVERE",
        included_unit_kinds=[
            "class",
            "struct",
            "enum",
            "extension",
            "actor",
            "function",
        ],
    )

    def test_phases_do_not_repeat_source_or_prior_outputs(self) -> None:
        verb = self._start()
        self.assertEqual([step.step_id for step in verb.steps], ["verb_count"])
        self.assertNotIn(self.review_unit, verb.steps[0].prompt)
        self.assertIn(self.review_unit_name, verb.steps[0].prompt)

        cohesion = self.sut.flow_next({
            verb.steps[0].instance_id: self._output_for("verb_count")
        })
        self.assertEqual(
            [step.step_id for step in cohesion.steps],
            ["cohesion_groups"],
        )
        self.assertNotIn(self.review_unit, cohesion.steps[0].prompt)
        self.assertNotIn("Canonical srp fixture evidence", cohesion.steps[0].prompt)

        stakeholder = self.sut.flow_next({
            cohesion.steps[0].instance_id: self._output_for("cohesion_groups")
        })
        self.assertEqual(
            [step.step_id for step in stakeholder.steps],
            ["stakeholder_count"],
        )
        self.assertNotIn(self.review_unit, stakeholder.steps[0].prompt)
        self.assertNotIn("Canonical srp fixture evidence", stakeholder.steps[0].prompt)

        exception = self.sut.flow_next({
            stakeholder.steps[0].instance_id: self._output_for("stakeholder_count")
        })
        self.assertEqual(
            [step.step_id for step in exception.steps],
            ["classify_exception"],
        )
        self.assertNotIn(self.review_unit, exception.steps[0].prompt)
        self.assertNotIn("Canonical srp fixture evidence", exception.steps[0].prompt)
