"""Proves aggregate retries expose an actionable partial-submission contract."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.aggregate_batch_step_presentation import (  # noqa: E402
    AggregateBatchStepPresentation,
)
from harness.batch_step_renderer_factory import BatchStepRendererFactory  # noqa: E402
from harness.first_ready_step_selector import FirstReadyStepSelector  # noqa: E402
from harness.flow_result_renderer import FlowResultRenderer  # noqa: E402
from harness.flow_run_orchestrator_factory import (  # noqa: E402
    FlowRunOrchestratorFactory,
)
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.sibling_batch_step_selector_factory import (  # noqa: E402
    SiblingBatchStepSelectorFactory,
)
from harness.single_step_renderer import SingleStepRenderer  # noqa: E402
from harness.step_formatter import StepFormatter  # noqa: E402
from harness.step_renderer import StepRenderer  # noqa: E402
from harness.subagent_delegator import SubagentDelegator  # noqa: E402
from harness.terminal_message_resolver import TerminalMessageResolver  # noqa: E402


"""
solid-name: TestAggregatePartialSubmissionRecovery
solid-category: integration-test
solid-spec: [SPEC-052]
solid-description: Verifies nested aggregate validation failures return unique pending addresses and partial-only correction guidance.
"""
class TestAggregatePartialSubmissionRecovery(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow_path = self._write_workflows()
        self.orchestrator = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()
        self.renderer = FlowResultRenderer(
            step_renderer=StepRenderer(
                ready_step_selector=FirstReadyStepSelector(),
                sibling_batch_selector=SiblingBatchStepSelectorFactory().make(),
                single_step_renderer=SingleStepRenderer(
                    subagent_delegator=SubagentDelegator(),
                    step_formatter=StepFormatter(),
                ),
                batch_step_renderer=BatchStepRendererFactory().make(),
            ),
            terminal_message_resolver=TerminalMessageResolver(),
        )

    def test_nested_rule_retry_contains_each_rejected_address_once(self) -> None:
        started, ready = self._start_review()

        remaining = self.orchestrator.flow_next(
            self._submission(
                ready.steps,
                invalid_steps={"secondary_count", "stakeholder_count"},
            )
        )

        self.assertIsNone(remaining.error, remaining.error)
        self.assertEqual(len(remaining.steps), 4)
        addresses = [
            self._address(step.batch)
            for step in remaining.steps
            if isinstance(step.batch, AggregateBatchStepPresentation)
        ]
        self.assertEqual(
            addresses,
            [
                ("AlphaType", "sample-rule", "secondary_count"),
                ("AlphaType", "sample-rule", "stakeholder_count"),
                ("BetaType", "sample-rule", "secondary_count"),
                ("BetaType", "sample-rule", "stakeholder_count"),
            ],
        )
        self.assertEqual(len(addresses), len(set(addresses)))
        completed = [
            event["instance_id"]
            for event in self._events(started.run_id)
            if event["event"] == "step_completed"
            and event["instance_id"] in {step.instance_id for step in ready.steps}
        ]
        self.assertEqual(len(completed), 4)

    def test_nested_item_specific_for_each_stays_outside_aggregate_compilation(self) -> None:
        workflow = self._write_nested_for_each_workflow()
        started = self.orchestrator.flow_start(str(workflow))
        discover = started.steps[0]
        self.assertIsInstance(discover.batch, AggregateBatchStepPresentation)
        assert isinstance(discover.batch, AggregateBatchStepPresentation)

        remaining = self.orchestrator.flow_next({
            discover.batch.label: {
                discover.batch.workflow_alias: {
                    discover.batch.authored_step.step_id: {
                        "candidates": [
                            {"name": "FirstCandidate"},
                            {"name": "SecondCandidate"},
                        ]
                    }
                }
            }
        })

        self.assertIsNone(remaining.error, remaining.error)
        self.assertEqual(len(remaining.steps), 2)
        self.assertTrue(all(step.batch is None for step in remaining.steps))
        rendered = self.renderer.render_next(remaining)
        self.assertIn("FirstCandidate", rendered)
        self.assertNotIn("SecondCandidate", rendered)

    def test_retry_explains_corrections_and_partial_json_resubmission(self) -> None:
        started, ready = self._start_review()
        remaining = self.orchestrator.flow_next(
            self._submission(
                ready.steps,
                invalid_steps={"secondary_count", "stakeholder_count"},
            )
        )

        rendered = self.renderer.render_next(remaining)

        self.assertIn("Accepted assignments are already saved", rendered)
        self.assertIn("Submit one JSON object containing only", rendered)
        self.assertIn("the pending or rejected assignments shown below", rendered)
        self.assertIn("Item: AlphaType", rendered)
        self.assertIn("Item: BetaType", rendered)
        self.assertIn("Workflow: sample-rule", rendered)
        self.assertIn("Step: secondary_count", rendered)
        self.assertEqual(rendered.count("not of type 'integer'"), 4)
        schema = json.loads(rendered[rendered.index("{"):])
        self.assertEqual(set(schema["required"]), {"AlphaType", "BetaType"})
        for item in ("AlphaType", "BetaType"):
            workflow = schema["properties"][item]["properties"]["sample-rule"]
            self.assertEqual(
                workflow["required"],
                ["secondary_count", "stakeholder_count"],
            )

        finished = self.orchestrator.flow_next(
            self._submission(remaining.steps, invalid_steps=set())
        )

        self.assertEqual(finished.status, "done", finished.error)
        completed = [
            event["instance_id"]
            for event in self._events(started.run_id)
            if event["event"] == "step_completed"
            and event["instance_id"] in {step.instance_id for step in ready.steps}
        ]
        self.assertEqual(len(completed), len(ready.steps))
        self.assertEqual(len(completed), len(set(completed)))

    def test_malformed_envelope_explains_full_json_resubmission(self) -> None:
        started, ready = self._start_review()

        rejected = self.orchestrator.flow_next({"srp": {}})

        self.assertEqual(rejected.status, "ready")
        self.assertIsNotNone(rejected.error)
        assert rejected.error is not None
        self.assertIn("Unknown aggregate item label 'srp'", rejected.error)
        self.assertIn("No assignments from this call were saved", rejected.error)
        self.assertIn("Resubmit the complete aggregate JSON", rejected.error)
        self.assertIn("Use the exact schema from the preceding", rejected.error)
        self.assertIn(
            "AlphaType / sample-rule / primary_count",
            rejected.error,
        )
        self.assertIn(
            "BetaType / sample-rule / classify_exception",
            rejected.error,
        )

        finished = self.orchestrator.flow_next(
            self._submission(ready.steps, invalid_steps=set())
        )

        self.assertEqual(finished.status, "done", finished.error)
        completed = [
            event["instance_id"]
            for event in self._events(started.run_id)
            if event["event"] == "step_completed"
            and event["instance_id"] in {step.instance_id for step in ready.steps}
        ]
        self.assertEqual(len(completed), len(ready.steps))
        self.assertEqual(len(completed), len(set(completed)))

    def _start_review(self):
        started = self.orchestrator.flow_start(str(self.workflow_path))
        ready = self.orchestrator.flow_next({
            started.steps[0].instance_id: {
                "units": [{"name": "AlphaType"}, {"name": "BetaType"}],
            }
        })
        self.assertIsNone(ready.error, ready.error)
        self.assertEqual(len(ready.steps), 8)
        return started, ready

    def _submission(
        self,
        steps,
        invalid_steps: set[str],
    ) -> dict[str, object]:
        submission: dict[str, object] = {}
        audit = {
            "reasoning": "The supplied unit supports this observation.",
            "evidence": "unit declaration",
        }
        for step in steps:
            presentation = step.batch
            self.assertIsInstance(presentation, AggregateBatchStepPresentation)
            assert isinstance(presentation, AggregateBatchStepPresentation)
            item = submission.setdefault(presentation.label, {})
            self.assertIsInstance(item, dict)
            workflow = item.setdefault(presentation.workflow_alias, {})
            self.assertIsInstance(workflow, dict)
            authored_step = presentation.authored_step.step_id
            if authored_step == "classify_exception":
                output = {"is_exception": False, "additional_info": audit}
            else:
                value: object = 1
                if authored_step in invalid_steps:
                    value = "not-an-integer"
                output = {"value": value, "additional_info": audit}
            workflow[authored_step] = output
        return submission

    @staticmethod
    def _address(
        presentation: AggregateBatchStepPresentation | None,
    ) -> tuple[str, str, str]:
        assert presentation is not None
        return (
            presentation.label,
            presentation.workflow_alias,
            presentation.authored_step.step_id,
        )

    def _write_workflows(self) -> Path:
        rule_directory = self.project_root / "workflows" / "review" / "sample-rule"
        rule_directory.mkdir(parents=True)
        (rule_directory / "workflow.yaml").write_text(
            textwrap.dedent(
                """
                id: sample-rule
                name: Sample Rule
                max_turns: 5
                rule:
                  scope: unit
                steps:
                  - id: primary_count
                    type: metric
                    metric_id: SAMPLE-1
                    prompt: Count primary concerns.
                    value: {type: integer, minimum: 0}
                    scoring:
                      severe: {operator: greater_than, value: 1}
                  - id: secondary_count
                    type: metric
                    metric_id: SAMPLE-2
                    prompt: Count secondary concerns.
                    depends_on: [primary_count]
                    value: {type: integer, minimum: 0}
                    scoring:
                      severe: {operator: greater_than, value: 1}
                  - id: stakeholder_count
                    type: metric
                    metric_id: SAMPLE-3
                    prompt: Count stakeholders.
                    depends_on: [secondary_count]
                    value: {type: integer, minimum: 0}
                    scoring:
                      severe: {operator: greater_than, value: 1}
                  - id: classify_exception
                    type: exception
                    prompt: Classify whether the unit is exempt.
                    depends_on: [stakeholder_count]
                """
            ),
            encoding="utf-8",
        )
        parent_directory = self.project_root / "workflows" / "review" / "aggregate"
        parent_directory.mkdir(parents=True)
        workflow_path = parent_directory / "workflow.yaml"
        workflow_path.write_text(
            textwrap.dedent(
                """
                id: aggregate-review
                name: Aggregate Review
                max_turns: 10
                steps:
                  - id: prepare
                    prompt: Prepare units.
                    outputs:
                      - name: units
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            additionalProperties: false
                            required: [name]
                            properties:
                              name: {type: string}
                  - group: aggregate_rules
                    execution:
                      mode: aggregate
                    presentation:
                      mode: combined
                    steps:
                      - include:
                          rules: all
                        as: rules
                        depends_on: [prepare]
                        for_each:
                          source: "{{steps.prepare.outputs.units}}"
                          mode: batch
                          label: "{{item.name}}"
                        with:
                          review_unit: "{{item}}"
                """
            ),
            encoding="utf-8",
        )
        return workflow_path

    def _write_nested_for_each_workflow(self) -> Path:
        child_directory = self.project_root / "workflows" / "candidate-review"
        child_directory.mkdir(parents=True)
        (child_directory / "workflow.yaml").write_text(
            textwrap.dedent(
                """
                id: candidate-review
                name: Candidate Review
                max_turns: 5
                execution:
                  mode: aggregate
                steps:
                  - id: discover
                    prompt: Discover candidates.
                    outputs:
                      - name: candidates
                        type: data
                        schema:
                          type: array
                          items:
                            type: object
                            additionalProperties: false
                            required: [name]
                            properties:
                              name: {type: string}
                  - id: classify
                    depends_on: [discover]
                    for_each: "{{steps.discover.outputs.candidates}}"
                    prompt: Classify {{item.name}}.
                    outputs:
                      - name: classification
                        type: data
                        schema: {type: string}
                """
            ),
            encoding="utf-8",
        )
        parent = self.project_root / "nested-for-each.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                id: nested-for-each
                name: Nested For Each
                max_turns: 5
                steps:
                  - include:
                      workflow: candidate-review
                    as: candidates
                """
            ),
            encoding="utf-8",
        )
        return parent

    def _events(self, run_id: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (
                self.project_root / "runs" / run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
        ]


if __name__ == "__main__":
    unittest.main()
