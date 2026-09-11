"""Validates declared output aggregation for included workflows."""

from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.runs_base_dir_resolver import RunsBaseDirResolver


"""
solid-name: TestWorkflowOutputAggregation
solid-category: test
solid-spec: [SPEC-037]
solid-description: Verifies included workflow outputs are exposed as ordered alias result envelopes.
"""
class TestWorkflowOutputAggregation(unittest.TestCase):

    def test_publishes_declared_outputs_in_source_order(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project_root = Path(temporary_directory.name)
        flow_path = self._write_workflows(project_root)
        orchestrator = self._make_orchestrator(project_root)

        started = orchestrator.flow_start(str(flow_path))
        children = orchestrator.flow_next({
            started.steps[0].instance_id: {
                "units": [
                    {"name": "Alpha", "enabled": True},
                    {"name": "Beta", "enabled": True},
                ],
            }
        })
        aggregated = orchestrator.flow_next({
            children.steps[1].instance_id: {"review": "Beta review"},
            children.steps[0].instance_id: {"review": "Alpha review"},
        })

        self.assertIsNone(aggregated.error, aggregated.error)
        self.assertEqual([step.step_id for step in aggregated.steps], ["aggregate"])
        result_json = aggregated.steps[0].prompt.removeprefix("Aggregate ").rstrip(".")
        self.assertEqual(
            json.loads(result_json),
            [
                {
                    "instance_id": "review-1",
                    "item": {"name": "Alpha", "enabled": True},
                    "outputs": {"review_results": "Alpha review"},
                },
                {
                    "instance_id": "review-2",
                    "item": {"name": "Beta", "enabled": True},
                    "outputs": {"review_results": "Beta review"},
                },
            ],
        )

    def test_omits_skipped_workflow_instances(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project_root = Path(temporary_directory.name)
        flow_path = self._write_workflows(project_root)
        orchestrator = self._make_orchestrator(project_root)

        started = orchestrator.flow_start(str(flow_path))
        children = orchestrator.flow_next({
            started.steps[0].instance_id: {
                "units": [
                    {"name": "Alpha", "enabled": True},
                    {"name": "Beta", "enabled": False},
                ],
            }
        })
        aggregated = orchestrator.flow_next({
            children.steps[0].instance_id: {"review": "Alpha review"},
        })

        result_json = aggregated.steps[0].prompt.removeprefix("Aggregate ").rstrip(".")
        results = json.loads(result_json)
        self.assertEqual([result["instance_id"] for result in results], ["review-1"])

    def test_empty_source_publishes_empty_results(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project_root = Path(temporary_directory.name)
        flow_path = self._write_workflows(project_root)
        orchestrator = self._make_orchestrator(project_root)

        started = orchestrator.flow_start(str(flow_path))
        aggregated = orchestrator.flow_next({
            started.steps[0].instance_id: {"units": []}
        })

        self.assertEqual(
            aggregated.steps[0].prompt,
            "Aggregate [].",
        )

    def test_non_iterated_include_publishes_one_result_envelope(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project_root = Path(temporary_directory.name)
        flow_path = self._write_non_iterated_workflows(project_root)
        orchestrator = self._make_orchestrator(project_root)

        child = orchestrator.flow_start(str(flow_path))
        aggregated = orchestrator.flow_next({
            child.steps[0].instance_id: {"review": "Complete"}
        })

        result_json = aggregated.steps[0].prompt.removeprefix("Aggregate ").rstrip(".")
        results = json.loads(result_json)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["instance_id"], "review-1")
        self.assertIsNone(results[0]["item"])

    def test_schema_mismatch_blocks_result_publication(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project_root = Path(temporary_directory.name)
        flow_path = self._write_non_iterated_workflows(project_root)
        orchestrator = self._make_orchestrator(project_root)

        child = orchestrator.flow_start(str(flow_path))
        blocked = orchestrator.flow_next({
            child.steps[0].instance_id: {"review": 42}
        })

        self.assertEqual(blocked.steps, [])
        self.assertIn("output 'review_results' is invalid", blocked.error)

    def test_aggregate_child_publishes_declared_output_after_all_steps_complete(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        project_root = Path(temporary_directory.name)
        (project_root / "child.yaml").write_text(
            textwrap.dedent(
                """
                id: aggregate-child
                name: Aggregate Child
                max_turns: 5
                execution:
                  mode: aggregate
                presentation:
                  mode: combined
                outputs:
                  - name: final_result
                    type: data
                    value: "{{steps.decide.outputs.result}}"
                    schema: {type: string}
                steps:
                  - id: inspect
                    prompt: Inspect.
                    outputs:
                      - name: analysis
                        type: data
                        schema: {type: string}
                  - id: decide
                    prompt: Decide.
                    depends_on: [inspect]
                    outputs:
                      - name: result
                        type: data
                        schema: {type: string}
                """
            ),
            encoding="utf-8",
        )
        parent = project_root / "parent.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                id: aggregate-parent
                name: Aggregate Parent
                max_turns: 5
                steps:
                  - include: child.yaml
                    as: child
                  - id: report
                    depends_on: [child]
                    prompt: Report {{workflows.child.results}}.
                """
            ),
            encoding="utf-8",
        )
        orchestrator = self._make_orchestrator(project_root)

        child = orchestrator.flow_start(str(parent))
        report = orchestrator.flow_next({
            "child-1": {
                "child": {
                    "inspect": {"analysis": "Inspected"},
                    "decide": {"result": "Accepted"},
                }
            }
        })

        self.assertEqual([step.step_id for step in report.steps], ["report"])
        self.assertIn("Accepted", report.steps[0].prompt)

    def _make_orchestrator(self, project_root: Path):
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: project_root
            ),
            plugin_root=project_root,
        ).build()

    def _write_non_iterated_workflows(self, project_root: Path) -> Path:
        (project_root / "child.yaml").write_text(
            textwrap.dedent(
                """
                id: child-review
                name: child_review
                outputs:
                  - name: review_results
                    type: data
                    value: "{{steps.review.outputs.review}}"
                    schema: {type: string}
                steps:
                  - id: review
                    prompt: Review the input.
                    outputs:
                      - name: review
                        type: data
                """
            ),
            encoding="utf-8",
        )
        parent = project_root / "parent.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                name: parent
                steps:
                  - include: child.yaml
                    as: review
                  - id: aggregate
                    depends_on: [review]
                    prompt: Aggregate {{workflows.review.results}}.
                """
            ),
            encoding="utf-8",
        )
        return parent

    def _write_workflows(self, project_root: Path) -> Path:
        (project_root / "child.yaml").write_text(
            textwrap.dedent(
                """
                id: child-review
                name: child_review
                outputs:
                  - name: review_results
                    type: data
                    value: "{{steps.review.outputs.review}}"
                    schema: {type: string}
                steps:
                  - id: review
                    prompt: Review {{params.review_unit.name}}.
                    outputs:
                      - name: review
                        type: data
                        schema: {type: string}
                """
            ),
            encoding="utf-8",
        )
        parent = project_root / "parent.yaml"
        parent.write_text(
            textwrap.dedent(
                """
                name: parent
                max_turns: 20
                steps:
                  - id: prepare
                    prompt: Prepare units.
                    outputs:
                      - name: units
                        type: data
                        schema:
                          type: array
                          items: {type: object}
                  - include: child.yaml
                    as: review
                    depends_on: [prepare]
                    for_each: "{{steps.prepare.outputs.units}}"
                    with:
                      review_unit: "{{item}}"
                    when:
                      ref: "{{item.enabled}}"
                      equals: true
                  - id: aggregate
                    depends_on: [review]
                    prompt: Aggregate {{workflows.review.results}}.
                """
            ),
            encoding="utf-8",
        )
        return parent
