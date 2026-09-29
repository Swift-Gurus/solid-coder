"""Validates co-located metrics inside included rule workflows."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.rule_declaration import RuleDeclaration
from harness.step_output_reference import StepOutputReference
from harness.workflow_catalog import WorkflowCatalog
from harness.workflow_source import WorkflowSource


class SingleWorkflowCatalogResolver:
    def __init__(self, source: WorkflowSource) -> None:
        self._source = source

    def resolve(
        self,
        workflow_id: str,
        search_paths: list[str],
    ) -> WorkflowSource | None:
        return self._source if workflow_id == self._source.id else None

    def catalog(self, search_paths: list[str]) -> WorkflowCatalog:
        return WorkflowCatalog(sources=[self._source])


"""
solid-name: TestCoLocatedMetricInclusion
solid-category: unit-test
solid-spec: [SPEC-058]
solid-description: Verifies normalized compact metrics retain nested workflow identity and membership.
"""
class TestCoLocatedMetricInclusion(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)

    def test_qualifies_metric_and_local_source_under_include_alias(self) -> None:
        child_path = self.directory / "child.yaml"
        child_path.write_text(
            textwrap.dedent(
                """
                id: child-rule
                name: Child Rule
                max_turns: 3
                rule: {}
                steps:
                  - id: classify
                    prompt: Classify observations.
                    outputs:
                      - name: observations
                        type: data
                        schema:
                          type: array
                          items: {type: string}
                    metrics:
                      - id: count
                        metric_id: TEST-1
                        value: {type: integer, minimum: 0}
                        scoring:
                          source: observations
                          severe: {operator: greater_than, value: 1}
                  - id: classify_exception
                    type: exception
                    depends_on: [count]
                    prompt: Classify the rule exception.
                """
            ),
            encoding="utf-8",
        )
        parent_path = self.directory / "parent.yaml"
        parent_path.write_text(
            textwrap.dedent(
                """
                id: parent
                name: Parent
                max_turns: 3
                steps:
                  - include:
                      workflow: child-rule
                    as: review
                """
            ),
            encoding="utf-8",
        )

        loader = FlowEngineAssemblyFactory().build(
            workflow_catalog_resolver=SingleWorkflowCatalogResolver(
                WorkflowSource(
                    id="child-rule",
                    entry_path=child_path,
                    package_root=None,
                    rule=RuleDeclaration(),
                )
            )
        ).flow_loader
        flow = loader.load(str(parent_path), [])

        self.assertEqual(
            [step.id for step in flow.steps],
            [
                "review.classify",
                "review.count",
                "review.classify_exception",
            ],
        )
        metric = flow.steps[1]
        self.assertEqual(metric.depends_on, ["review.classify"])
        self.assertEqual(
            metric.metric_calculation.source,
            StepOutputReference(
                step_id="review.classify",
                output_name="observations",
            ),
        )
        review_group = next(
            group for group in flow.alias_groups if group.alias == "review"
        )
        self.assertEqual(
            review_group.member_ids,
            [
                "review.classify",
                "review.classify_exception",
                "review.count",
            ],
        )


if __name__ == "__main__":
    unittest.main()
