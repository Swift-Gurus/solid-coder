"""Validates one model turn can complete several existing for-each instances."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.batch_step_renderer import BatchStepRenderer
from harness.batch_step_item_renderer import BatchStepItemRenderer
from harness.first_ready_step_selector import FirstReadyStepSelector
from harness.flow_run_orchestrator import FlowRunOrchestrator
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from harness.sibling_batch_step_selector import SiblingBatchStepSelector
from harness.single_step_renderer import SingleStepRenderer
from harness.step_formatter import StepFormatter
from harness.step_renderer import StepRenderer
from harness.subagent_delegator import SubagentDelegator


_FLOW = """
    id: batch-review
    name: Batched Review
    max_turns: 10
    steps:
      - id: prepare
        prompt: Prepare review units.
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

      - id: review
        prompt: Assess every listed unit using the shared rule.
        depends_on: [prepare]
        for_each:
          source: "{{steps.prepare.outputs.units}}"
          mode: batch
          label: "{{item.name}}"
        outputs:
          - name: result
            type: data
            schema: {type: string}

      - id: summarize
        prompt: Summarize {{steps.review.outputs.result}}
        depends_on: [review]
"""


"""
solid-name: TestBatchedForEachFlowIntegration
solid-category: integration-test
solid-spec: [SPEC-042]
solid-description: Proves batched presentation hides engine identity while domain-keyed submissions retain ordinary per-instance completion, retry, fan-in, and replay.
"""
class TestBatchedForEachFlowIntegration(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.flow_path = self.project_root / "workflow.yaml"
        self.flow_path.write_text(textwrap.dedent(_FLOW), encoding="utf-8")
        self.sut = self._orchestrator()
        self.renderer = StepRenderer(
            ready_step_selector=FirstReadyStepSelector(),
            sibling_batch_selector=SiblingBatchStepSelector(),
            single_step_renderer=SingleStepRenderer(
                subagent_delegator=SubagentDelegator(),
                step_formatter=StepFormatter(),
            ),
            batch_step_renderer=BatchStepRenderer(
                item_renderer=BatchStepItemRenderer()
            ),
        )

    def test_renders_shared_prompt_once_with_domain_labels_only(self) -> None:
        ready = self._start_batch()

        rendered = self.renderer.render_steps(ready.steps)

        self.assertEqual(
            rendered.count("Assess every listed unit using the shared rule."),
            1,
        )
        self.assertIn("Alpha", rendered)
        self.assertIn("Beta", rendered)
        self.assertNotIn("review-1", rendered)
        self.assertNotIn("review-2", rendered)

    def test_domain_keyed_submission_completes_existing_instances(self) -> None:
        self._start_batch()

        result = self.sut.flow_next(
            {
                "Alpha": {"result": "Alpha result"},
                "Beta": {"result": "Beta result"},
            }
        )

        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        self.assertIn("Alpha result", result.steps[0].prompt)
        self.assertIn("Beta result", result.steps[0].prompt)

    def test_partial_submission_presents_only_the_missing_domain_label(self) -> None:
        self._start_batch()

        ready = self.sut.flow_next(
            {"Alpha": {"result": "Alpha result"}}
        )
        rendered = self.renderer.render_steps(ready.steps)

        self.assertNotIn("Alpha", rendered)
        self.assertIn("Beta", rendered)
        self.assertNotIn("review-2", rendered)

    def test_replay_preserves_partial_domain_completion(self) -> None:
        self._start_batch()
        self.sut.flow_next({"Alpha": {"result": "Alpha result"}})

        ready = self._orchestrator().flow_next()
        rendered = self.renderer.render_steps(ready.steps)

        self.assertNotIn("Alpha", rendered)
        self.assertIn("Beta", rendered)

    def test_invalid_item_retries_only_its_domain_label_with_reason(self) -> None:
        self._start_batch()

        ready = self.sut.flow_next({
            "Alpha": {"result": 123},
            "Beta": {"result": "Beta result"},
        })
        rendered = self.renderer.render_steps(ready.steps)

        self.assertEqual([step.batch.label for step in ready.steps], ["Alpha"])
        self.assertIn("Alpha", rendered)
        self.assertNotIn("Beta", rendered)
        self.assertIn("not of type 'string'", rendered)
        self.assertNotIn(ready.steps[0].instance_id, rendered)

    def test_malformed_item_retries_without_exposing_internal_identity(self) -> None:
        self._start_batch()

        ready = self.sut.flow_next({
            "Alpha": "not an output object",
            "Beta": {"result": "Beta result"},
        })
        rendered = self.renderer.render_steps(ready.steps)

        self.assertEqual([step.batch.label for step in ready.steps], ["Alpha"])
        self.assertIn("must be an object", rendered)
        self.assertNotIn(ready.steps[0].instance_id, rendered)

    def test_unknown_domain_label_is_rejected_without_completing_a_unit(self) -> None:
        self._start_batch()

        result = self.sut.flow_next(
            {"Gamma": {"result": "Invented result"}}
        )

        self.assertEqual(result.status, "ready")
        self.assertIn("unknown", result.error.lower())
        ready = self.sut.flow_next()
        self.assertEqual(
            [step.batch.label for step in ready.steps],
            ["Alpha", "Beta"],
        )

    def test_included_workflow_instances_share_one_batched_child_step(self) -> None:
        subflows = self.project_root / "subflows"
        subflows.mkdir()
        child_path = subflows / "child.yaml"
        child_path.write_text(textwrap.dedent("""
            id: child-review
            name: Child Review
            outputs:
              - name: result
                type: data
                value: "{{steps.assess.outputs.result}}"
                schema: {type: string}
            steps:
              - id: assess
                prompt: Assess every listed unit using the shared child rule.
                outputs:
                  - name: result
                    type: data
                    schema: {type: string}
        """), encoding="utf-8")
        parent_path = self.project_root / "parent.yaml"
        parent_path.write_text(textwrap.dedent("""
            id: parent-review
            name: Parent Review
            max_turns: 10
            steps:
              - id: prepare
                prompt: Prepare review units.
                outputs:
                  - name: units
                    type: data
                    schema: {type: array, items: {type: object}}
              - include: child.yaml
                as: reviews
                depends_on: [prepare]
                for_each:
                  source: "{{steps.prepare.outputs.units}}"
                  mode: batch
                  label: "{{item.name}}"
                with:
                  review_unit: "{{item}}"
              - id: summarize
                depends_on: [reviews]
                prompt: Summarize {{workflows.reviews.results}}.
        """), encoding="utf-8")
        sut = self._orchestrator()
        started = sut.flow_start(str(parent_path))
        ready = sut.flow_next({
            started.steps[0].instance_id: {
                "units": [{"name": "Alpha"}, {"name": "Beta"}]
            }
        })

        rendered = self.renderer.render_steps(ready.steps)

        self.assertEqual(
            rendered.count("Assess every listed unit using the shared child rule."),
            1,
        )
        self.assertIn("Alpha", rendered)
        self.assertIn("Beta", rendered)
        result = sut.flow_next({
            "Alpha": {"result": "Alpha result"},
            "Beta": {"result": "Beta result"},
        })
        self.assertEqual([step.step_id for step in result.steps], ["summarize"])
        self.assertIn("Alpha result", result.steps[0].prompt)
        self.assertIn("Beta result", result.steps[0].prompt)

    def _start_batch(self):
        started = self.sut.flow_start(str(self.flow_path))
        return self.sut.flow_next(
            {
                started.steps[0].instance_id: {
                    "units": [
                        {"name": "Alpha"},
                        {"name": "Beta"},
                    ]
                }
            }
        )

    def _orchestrator(self) -> FlowRunOrchestrator:
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()


if __name__ == "__main__":
    unittest.main()
