"""Proves several applicable batched rules can share one model turn."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.batch_step_renderer_factory import BatchStepRendererFactory  # noqa: E402
from harness.first_ready_step_selector import FirstReadyStepSelector  # noqa: E402
from harness.flow_validation_error import FlowValidationError  # noqa: E402
from harness.flow_run_orchestrator import FlowRunOrchestrator  # noqa: E402
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.sibling_batch_step_selector_factory import (  # noqa: E402
    SiblingBatchStepSelectorFactory,
)
from harness.single_step_renderer import SingleStepRenderer  # noqa: E402
from harness.step_formatter import StepFormatter  # noqa: E402
from harness.step_renderer import StepRenderer  # noqa: E402
from harness.subagent_delegator import SubagentDelegator  # noqa: E402


"""
solid-name: TestCombinedRulePresentation
solid-category: integration-test
solid-spec: [SPEC-043]
solid-description: Proves combined presentation follows applicability while preserving per-rule and per-unit completion, retries, and replay.
"""
class TestCombinedRulePresentation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        self.workflow_path = self._write_workflows()
        self.sut = self._orchestrator()
        self.renderer = StepRenderer(
            ready_step_selector=FirstReadyStepSelector(),
            sibling_batch_selector=SiblingBatchStepSelectorFactory().make(),
            single_step_renderer=SingleStepRenderer(
                subagent_delegator=SubagentDelegator(),
                step_formatter=StepFormatter(),
            ),
            batch_step_renderer=BatchStepRendererFactory().make(),
        )

    def test_renders_each_applicable_rule_once_with_its_unit_subset(self) -> None:
        ready = self._start_combined_review()

        rendered = self.renderer.render_steps(ready.steps)

        self.assertEqual(rendered.count("Apply the alpha rule."), 1)
        self.assertEqual(rendered.count("Apply the protocol rule."), 1)
        self.assertIn("AlphaType", rendered)
        self.assertIn("BetaProtocol", rendered)
        self.assertIn("alpha", rendered)
        self.assertIn("protocol_only", rendered)
        self.assertNotIn(ready.steps[0].instance_id, rendered)

    def test_nested_submission_completes_existing_instances(self) -> None:
        started, ready = self._start_combined_review_with_run()

        result = self.sut.flow_next({
            "AlphaType": {
                "alpha": {"finding": "Alpha finding"},
            },
            "BetaProtocol": {
                "alpha": {"finding": "Beta alpha finding"},
                "protocol_only": {"finding": "Beta protocol finding"},
            },
        })

        self.assertEqual(result.status, "done", result.error)
        completed = [
            event
            for event in self._events(started.run_id)
            if event.get("event") == "step_completed"
            and event.get("instance_id")
            in {step.instance_id for step in ready.steps}
        ]
        self.assertEqual(len(completed), 3)

    def test_partial_submission_and_replay_return_only_missing_pairs(self) -> None:
        self._start_combined_review_with_run()

        partial = self.sut.flow_next({
            "AlphaType": {
                "alpha": {"finding": "Alpha finding"},
            },
            "BetaProtocol": {
                "protocol_only": {"finding": "Beta protocol finding"},
            },
        })
        replayed = self._orchestrator().flow_next()
        rendered = self.renderer.render_steps(replayed.steps)

        self.assertEqual(partial.status, "ready", partial.error)
        self.assertEqual(replayed.status, "ready", replayed.error)
        self.assertNotIn("AlphaType", rendered)
        self.assertIn("BetaProtocol", rendered)
        self.assertIn("alpha", rendered)
        self.assertNotIn("protocol_only", rendered)

    def test_invalid_pair_retries_only_that_existing_instance(self) -> None:
        _, ready = self._start_combined_review_with_run()
        beta_alpha = next(
            step
            for step in ready.steps
            if step.batch is not None
            and step.batch.label == "BetaProtocol"
            and "Apply the alpha rule." in step.prompt
        )

        retried = self.sut.flow_next({
            "AlphaType": {
                "alpha": {"finding": "Alpha finding"},
            },
            "BetaProtocol": {
                "alpha": {"finding": 123},
                "protocol_only": {"finding": "Beta protocol finding"},
            },
        })
        rendered = self.renderer.render_steps(retried.steps)

        self.assertEqual(retried.status, "ready", retried.error)
        self.assertEqual([step.instance_id for step in retried.steps], [beta_alpha.instance_id])
        self.assertIn("BetaProtocol", rendered)
        self.assertIn("alpha", rendered)
        self.assertIn("not of type 'string'", rendered)
        self.assertNotIn(beta_alpha.instance_id, rendered)

    def test_unknown_rule_alias_is_rejected_without_completing_work(self) -> None:
        _, ready = self._start_combined_review_with_run()

        rejected = self.sut.flow_next({
            "AlphaType": {
                "invented": {"finding": "Invented finding"},
            }
        })
        still_ready = self.sut.flow_next()

        self.assertEqual(rejected.status, "ready")
        self.assertIn("unknown", rejected.error.lower())
        self.assertEqual(
            {step.instance_id for step in still_ready.steps},
            {step.instance_id for step in ready.steps},
        )

    def test_unknown_item_label_is_rejected_without_completing_work(self) -> None:
        _, ready = self._start_combined_review_with_run()

        rejected = self.sut.flow_next({
            "InventedType": {
                "alpha": {"finding": "Invented finding"},
            }
        })
        still_ready = self.sut.flow_next()

        self.assertEqual(rejected.status, "ready")
        self.assertIn("unknown", rejected.error.lower())
        self.assertEqual(
            {step.instance_id for step in still_ready.steps},
            {step.instance_id for step in ready.steps},
        )

    def test_rejects_unknown_presentation_mode(self) -> None:
        invalid = self.project_root / "invalid-mode.yaml"
        invalid.write_text(
            textwrap.dedent(
                """
                id: invalid-mode
                name: Invalid Mode
                steps:
                  - group: reviews
                    presentation:
                      mode: invented
                    steps:
                      - id: assess
                        prompt: Assess.
                """
            ),
            encoding="utf-8",
        )

        with self.assertRaises(FlowValidationError):
            self.sut.flow_start(str(invalid))

    def test_rejects_non_batched_child_of_combined_group(self) -> None:
        invalid = self.project_root / "invalid-child.yaml"
        invalid.write_text(
            textwrap.dedent(
                """
                id: invalid-child
                name: Invalid Child
                steps:
                  - group: reviews
                    presentation:
                      mode: combined
                    steps:
                      - include: alpha-rule.yaml
                        as: alpha
                """
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "batch",
        ):
            self.sut.flow_start(str(invalid))

    def _start_combined_review(self):
        return self._start_combined_review_with_run()[1]

    def _start_combined_review_with_run(self):
        started = self.sut.flow_start(str(self.workflow_path))
        ready = self.sut.flow_next({
            started.steps[0].instance_id: {
                "units": [
                    {"name": "AlphaType", "kind": "class"},
                    {"name": "BetaProtocol", "kind": "protocol"},
                ]
            }
        })
        self.assertIsNone(ready.error, ready.error)
        self.assertEqual(len(ready.steps), 3)
        return started, ready

    def _write_workflows(self) -> Path:
        self._write_rule("alpha-rule.yaml", "Apply the alpha rule.")
        self._write_rule("protocol-rule.yaml", "Apply the protocol rule.")
        workflow_path = self.project_root / "combined.yaml"
        workflow_path.write_text(
            textwrap.dedent(
                """
                id: combined-review
                name: Combined Review
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
                            required: [name, kind]
                            properties:
                              name: {type: string}
                              kind: {type: string}

                  - group: combined_rules
                    presentation:
                      mode: combined
                    steps:
                      - include: alpha-rule.yaml
                        as: alpha
                        depends_on: [prepare]
                        for_each:
                          source: "{{steps.prepare.outputs.units}}"
                          mode: batch
                          label: "{{item.name}}"
                        with:
                          review_unit: "{{item}}"

                      - include: protocol-rule.yaml
                        as: protocol_only
                        depends_on: [prepare]
                        for_each:
                          source: "{{steps.prepare.outputs.units}}"
                          mode: batch
                          label: "{{item.name}}"
                        with:
                          review_unit: "{{item}}"
                        when:
                          ref: "{{item.kind}}"
                          equals: protocol
                """
            ),
            encoding="utf-8",
        )
        return workflow_path

    def _write_rule(self, filename: str, prompt: str) -> None:
        (self.project_root / filename).write_text(
            textwrap.dedent(
                f"""
                id: {Path(filename).stem}
                name: {Path(filename).stem}
                max_turns: 3
                steps:
                  - id: assess
                    prompt: {prompt}
                    outputs:
                      - name: finding
                        type: data
                        schema: {{type: string}}
                """
            ),
            encoding="utf-8",
        )

    def _events(self, run_id: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (
                self.project_root / "runs" / run_id / "events.jsonl"
            ).read_text(encoding="utf-8").splitlines()
        ]

    def _orchestrator(self) -> FlowRunOrchestrator:
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.project_root
            ),
            plugin_root=self.project_root,
        ).build()


if __name__ == "__main__":
    unittest.main()
