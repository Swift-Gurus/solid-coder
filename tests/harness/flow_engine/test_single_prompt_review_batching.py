"""Verifies batching in the experimental single-prompt file review."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from harness.batch_step_presentation_mode import BatchStepPresentationMode  # noqa: E402
from harness.batch_step_renderer_factory import BatchStepRendererFactory  # noqa: E402
from harness.first_ready_step_selector import FirstReadyStepSelector  # noqa: E402
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory  # noqa: E402
from harness.flow_loading import FlowLoading  # noqa: E402
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory  # noqa: E402
from harness.project_context import ProjectDirectory  # noqa: E402
from harness.runs_base_dir_resolver import RunsBaseDirResolver  # noqa: E402
from harness.sibling_batch_step_selector_factory import (  # noqa: E402
    SiblingBatchStepSelectorFactory,
)
from harness.single_step_renderer import SingleStepRenderer  # noqa: E402
from harness.step_formatter import StepFormatter  # noqa: E402
from harness.step_renderer import StepRenderer  # noqa: E402
from harness.subagent_delegator import SubagentDelegator  # noqa: E402
from review.review_operation_registrations_factory import (  # noqa: E402
    ReviewOperationRegistrationsFactory,
)
from source.source_operation_registrations_factory import (  # noqa: E402
    SourceOperationRegistrationsFactory,
)


"""
solid-name: TestSinglePromptReviewBatching
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-042]
solid-description: Proves shared single-prompt review rules batch normalized units while rules requiring unit-specific search context remain individually presented.
"""
class TestSinglePromptReviewBatching(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        project_directory = ProjectDirectory(path=self.run_root)
        registrations = [
            *SourceOperationRegistrationsFactory(
                project_directory=project_directory,
            ).make(),
            *ReviewOperationRegistrationsFactory().make(),
        ]
        self.sut = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: self.run_root,
            ),
            plugin_root=_PROJECT_ROOT,
            project_directory=project_directory,
            operation_registrations=registrations,
        ).build()
        self.renderer = StepRenderer(
            ready_step_selector=FirstReadyStepSelector(),
            sibling_batch_selector=SiblingBatchStepSelectorFactory().make(),
            single_step_renderer=SingleStepRenderer(
                subagent_delegator=SubagentDelegator(),
                step_formatter=StepFormatter(),
            ),
            batch_step_renderer=BatchStepRendererFactory().make(),
        )

    def test_batches_shared_rule_prompts_and_keeps_search_rules_individual(self) -> None:
        started = self.sut.flow_start("solid-file-review-single-prompt")
        source = textwrap.dedent(
            """
            final class ProfileLoader {
                func load() {}
            }

            struct ProfileEnvelope {
                let name: String
            }
            """
        ).lstrip()

        ready = self.sut.flow_next({
            started.steps[0].instance_id: {
                "target": {
                    "kind": "text",
                    "text": source,
                    "virtual_path": str(self.run_root / "Profile.swift"),
                }
            }
        })

        combined_steps = []
        for local_step_id in ("assess_srp", "assess_ocp", "assess_lsp"):
            steps = [step for step in ready.steps if step.step_id.endswith(local_step_id)]
            self.assertEqual(len(steps), 2)
            self.assertTrue(all(step.batch is not None for step in steps))
            self.assertTrue(
                all(
                    step.batch.mode is BatchStepPresentationMode.COMBINED_RULES
                    for step in steps
                    if step.batch is not None
                )
            )
            self.assertEqual(len({step.prompt for step in steps}), 1)
            combined_steps.extend(steps)

        rendered = self.renderer.render_steps(combined_steps)
        self.assertEqual(rendered.count("Rule: srp_reviews"), 1)
        self.assertEqual(rendered.count("Rule: ocp_reviews"), 1)
        self.assertEqual(rendered.count("Rule: lsp_reviews"), 1)
        self.assertNotIn(source, rendered)

        dry_steps = [step for step in ready.steps if step.step_id.endswith("generate_terms")]
        self.assertEqual(len(dry_steps), 2)
        self.assertTrue(all(step.batch is None for step in dry_steps))

    def test_single_prompt_rule_contracts_preserve_authored_metrics(self) -> None:
        loader = FlowEngineAssemblyFactory().build().flow_loader

        self._assert_rule_contract(
            loader,
            "srp-single-prompt",
            ["SRP-1", "SRP-2", "SRP-3"],
            ["verb_count", "cohesion_groups", "stakeholder_count", "exception"],
        )
        self._assert_rule_contract(
            loader,
            "ocp-single-prompt",
            ["OCP-1", "OCP-2", "OCP-3"],
            [
                "dependencies",
                "has_hardcoded_behavior_selection",
                "testability",
                "sealed_variation_points",
                "untestable_dependencies",
                "testable_direct_count",
                "exception",
            ],
        )
        self._assert_rule_contract(
            loader,
            "lsp-single-prompt",
            ["LSP-1", "LSP-2", "LSP-3", "LSP-4"],
            [
                "type_check_analysis",
                "inheritance_analysis",
                "contract_implementations",
                "type_checks",
                "contract_violations",
                "fatal_error_methods",
                "empty_methods",
                "exception",
            ],
        )

    def _assert_rule_contract(
        self,
        loader: FlowLoading,
        workflow_id: str,
        metric_ids: list[str],
        output_names: list[str],
    ) -> None:
        path = (
            _PROJECT_ROOT
            / "workflows"
            / "review"
            / "experiments"
            / workflow_id
            / "workflow.yaml"
        )
        flow = loader.load(str(path), [str(_PROJECT_ROOT / "workflows")])
        assessment = flow.steps[0].assessment

        self.assertIsNotNone(assessment)
        self.assertEqual(
            [metric.metric_id for metric in assessment.metrics],
            metric_ids,
        )
        self.assertEqual(
            [output.name for output in flow.steps[0].outputs],
            output_names,
        )


if __name__ == "__main__":
    unittest.main()
