"""Verifies the one-call SRP prompt-shape experiment."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_HARNESS_DIRECTORY = Path(__file__).resolve().parents[1]
for _directory in (_PROJECT_ROOT / "mcp-server", _HARNESS_DIRECTORY):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.static_session_id_reader import StaticSessionIdReader  # noqa: E402
from review_unit_workflow_context import ReviewUnitWorkflowContext  # noqa: E402
from review_unit_workflow_parameters import ReviewUnitWorkflowParameters  # noqa: E402
from review_unit_workflow_target import ReviewUnitWorkflowTarget  # noqa: E402
from rule_instruction_block_reader import RuleInstructionBlockReader  # noqa: E402


"""
solid-name: TestSRPSinglePromptValidationFlow
solid-category: integration-test
solid-spec: [SPEC-036]
solid-description: Proves the experimental SRP workflow presents one canonical prompt and validates all audited observations in one response.
"""
class TestSRPSinglePromptValidationFlow(unittest.TestCase):
    WORKFLOW_ID = "srp-single-prompt"

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.review_unit = (
            _PROJECT_ROOT
            / "tests"
            / "principles"
            / "SRP"
            / "fixtures"
            / "fixture-1.swift"
        ).read_text(encoding="utf-8")
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.run_root,
            ),
            plugin_root=_PROJECT_ROOT,
            session_reader=StaticSessionIdReader("srp-single-prompt-test"),
        ).build()

    def test_starts_exactly_one_step_with_complete_canonical_instructions(self) -> None:
        started = self._start()

        self.assertEqual([step.step_id for step in started.steps], ["assess_srp"])
        prompt = started.steps[0].prompt
        self.assertNotIn(self.review_unit, prompt)
        self.assertNotIn("fixture-1.swift", prompt)
        self.assertIn("the supplied review unit", prompt)
        rule = (
            _PROJECT_ROOT / "references" / "principles" / "SRP" / "rule.md"
        ).read_text(encoding="utf-8")
        reader = RuleInstructionBlockReader()
        for metric_id, name in (
            ("SRP-1", "Verb Count"),
            ("SRP-2", "Cohesion Groups"),
            ("SRP-3", "Stakeholder Count"),
        ):
            self.assertIn(reader.definition(rule, metric_id, name), prompt)
            self.assertIn(reader.detection(rule, metric_id, name), prompt)
        self.assertIn(reader.exceptions(rule), prompt)

    def test_rejects_an_incomplete_aggregate_response(self) -> None:
        started = self._start()

        rejected = self.sut.flow_next({
            started.steps[0].instance_id: {
                "verb_count": self._measurement(6),
            }
        })

        self.assertEqual(rejected.status, "ready")
        self.assertEqual(len(rejected.steps), 1)
        self.assertIn("cohesion_groups", rejected.steps[0].rejection_reason)

    def test_completes_after_one_audited_aggregate_response(self) -> None:
        started = self._start()

        completed = self.sut.flow_next({
            started.steps[0].instance_id: self._response(),
        })

        self.assertEqual(completed.status, "done", completed.error)
        self.assertEqual(completed.steps, [])
        events = [
            json.loads(line)
            for line in (
                self.run_root / "runs" / started.run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        completed_steps = [
            event for event in events if event.get("event") == "step_completed"
        ]
        self.assertEqual(len(completed_steps), 1)
        self.assertEqual(completed_steps[0]["outputs"], self._response())

    def test_batched_include_completes_two_units_in_one_submission(self) -> None:
        parent = self.run_root / "workflow.yaml"
        parent.write_text(textwrap.dedent("""
            id: batched-srp-review
            name: Batched SRP Review
            max_turns: 5
            steps:
              - id: prepare
                prompt: Prepare units.
                outputs:
                  - name: units
                    type: data
                    schema: {type: array, items: {type: object}}
              - include:
                  workflow: srp-single-prompt
                as: srp_reviews
                depends_on: [prepare]
                for_each:
                  source: "{{steps.prepare.outputs.units}}"
                  mode: batch
                  label: "{{item.target.name}}"
                with:
                  review_unit: "{{item}}"
        """), encoding="utf-8")
        started = self.sut.flow_start(str(parent))
        ready = self.sut.flow_next({
            started.steps[0].instance_id: {
                "units": [
                    ReviewUnitWorkflowContext(
                        target=ReviewUnitWorkflowTarget(name="Alpha")
                    ).model_dump(),
                    ReviewUnitWorkflowContext(
                        target=ReviewUnitWorkflowTarget(name="Beta")
                    ).model_dump(),
                ]
            }
        })

        self.assertEqual(
            [step.batch.label for step in ready.steps],
            ["Alpha", "Beta"],
        )
        self.assertEqual(len({step.prompt for step in ready.steps}), 1)
        completed = self.sut.flow_next({
            "Alpha": self._response(),
            "Beta": self._response(),
        })

        self.assertEqual(completed.status, "done", completed.error)
        events = [
            json.loads(line)
            for line in (
                self.run_root / "runs" / started.run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        completed_srp = [
            event
            for event in events
            if event.get("event") == "step_completed"
            and event.get("local_step_id") == "assess_srp"
        ]
        self.assertEqual(len(completed_srp), 2)

    def _start(self):
        parameters = ReviewUnitWorkflowParameters(
            review_unit=ReviewUnitWorkflowContext(
                target=ReviewUnitWorkflowTarget(name="fixture-1.swift")
            )
        )
        return self.sut.flow_start(self.WORKFLOW_ID, parameters.model_dump())

    @staticmethod
    def _measurement(value: int) -> dict[str, object]:
        return {
            "value": value,
            "additional_info": {
                "reasoning": "Measured from the supplied unit.",
                "evidence": "Precise fixture evidence.",
            },
        }

    def _response(self) -> dict[str, object]:
        return {
            "verb_count": self._measurement(6),
            "cohesion_groups": self._measurement(2),
            "stakeholder_count": self._measurement(2),
            "exception": {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "The fixture is not a facade or coordinator.",
                    "evidence": "Its dependencies are concrete and methods contain behavior.",
                },
            },
        }


if __name__ == "__main__":
    unittest.main()
