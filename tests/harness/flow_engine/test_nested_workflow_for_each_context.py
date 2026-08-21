"""Validates nested workflow iteration context and result publication."""

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
solid-name: TestNestedWorkflowForEachContext
solid-category: integration-test
solid-spec: [SPEC-037, SPEC-040]
solid-description: Proves child for-each steps receive their own item while retaining parent inputs, skips, and declared results.
"""
class TestNestedWorkflowForEachContext(unittest.TestCase):

    def test_inner_iteration_uses_candidate_item_and_parent_target_input(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project_root = Path(temporary.name)
        parent = self._write_workflows(project_root)
        orchestrator = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: project_root
            ),
            plugin_root=project_root,
        ).build()

        prepared = orchestrator.flow_start(str(parent))
        child = orchestrator.flow_next({
            prepared.steps[0].instance_id: {
                "targets": [
                    {"identity": "target-1", "name": "UserLoader"},
                    {"identity": "target-2", "name": "ImageCache"},
                ]
            }
        })
        classification = orchestrator.flow_next({
            step.instance_id: {
                "candidates": (
                    [
                        {
                            "kind": "loaded",
                            "candidate": {
                                "source_identity": "SharedLoader.swift"
                            },
                        },
                        {
                            "kind": "missing",
                            "candidate": {
                                "source_identity": "DeletedLoader.swift"
                            },
                        },
                    ]
                    if "UserLoader" in step.prompt
                    else [
                        {
                            "kind": "missing",
                            "candidate": {
                                "source_identity": "DeletedCache.swift"
                            },
                        }
                    ]
                )
            }
            for step in child.steps
        })

        self.assertIsNone(classification.error, classification.error)
        self.assertEqual(len(classification.steps), 1)
        self.assertTrue(
            classification.steps[0].prompt.startswith(
            "Compare UserLoader with SharedLoader.swift",
            ),
        )
        aggregated = orchestrator.flow_next({
            classification.steps[0].instance_id: {
                "assessment": {
                    "classification": "EXACT",
                    "reasoning": "The existing unit owns the same behavior.",
                    "evidence": "Both expose the same loading sequence.",
                }
            }
        })

        result_json = aggregated.steps[0].prompt.removeprefix("Aggregate ")
        results = json.loads(result_json)
        self.assertEqual(results[0]["item"]["identity"], "target-1")
        self.assertEqual(
            results[0]["outputs"]["classifications"],
            [{
                "classification": "EXACT",
                "reasoning": "The existing unit owns the same behavior.",
                "evidence": "Both expose the same loading sequence.",
            }],
        )
        self.assertEqual(results[1]["item"]["identity"], "target-2")
        self.assertEqual(results[1]["outputs"]["classifications"], [])

    @staticmethod
    def _write_workflows(project_root: Path) -> Path:
        child = project_root / "child.yaml"
        child.write_text(textwrap.dedent(
            """
            id: candidate-review
            name: Candidate Review
            outputs:
              - name: classifications
                type: data
                value: "{{steps.classify.outputs.assessment}}"
                schema:
                  type: array
                  items:
                    type: object
                    additionalProperties: false
                    required: [classification, reasoning, evidence]
                    properties:
                      classification: {type: string}
                      reasoning: {type: string}
                      evidence: {type: string}
            steps:
              - id: prepare
                prompt: Prepare candidates for {{params.target.name}}
                outputs:
                  - name: candidates
                    type: data
                    schema: {type: array, items: {type: object}}
              - id: classify
                depends_on: [prepare]
                for_each: "{{steps.prepare.outputs.candidates}}"
                when:
                  ref: "{{item.kind}}"
                  equals: loaded
                prompt: Compare {{params.target.name}} with {{item.candidate.source_identity}}
                outputs:
                  - name: assessment
                    type: data
                    schema:
                      type: object
                      additionalProperties: false
                      required: [classification, reasoning, evidence]
                      properties:
                        classification: {type: string}
                        reasoning: {type: string}
                        evidence: {type: string}
            """
        ), encoding="utf-8")
        parent = project_root / "parent.yaml"
        parent.write_text(textwrap.dedent(
            """
            name: Nested Candidate Review
            max_turns: 10
            steps:
              - id: prepare
                prompt: Prepare targets
                outputs:
                  - name: targets
                    type: data
                    schema: {type: array, items: {type: object}}
              - include: child.yaml
                as: search
                depends_on: [prepare]
                for_each: "{{steps.prepare.outputs.targets}}"
                with:
                  target: "{{item}}"
              - id: aggregate
                depends_on: [search]
                prompt: Aggregate {{workflows.search.results}}
            """
        ), encoding="utf-8")
        return parent


if __name__ == "__main__":
    unittest.main()
