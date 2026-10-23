"""Validates generic pairwise metric declarations through the real loader."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_validation_error import FlowValidationError

"""
solid-name: TestComponentMetricLoading
solid-category: unit-test
solid-spec: [SPEC-059]
solid-description: Verifies pairwise reducer declaration and source-schema rejection before workflow execution.
"""


class TestComponentMetricLoading(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "workflow.yaml"
        self.assembly = FlowEngineAssemblyFactory().build()
        self.source = (
            Path(__file__).resolve().parents[1]
            / "fixtures/component_count/workflow.yaml"
        ).read_text(encoding="utf-8")

    def test_loads_co_located_component_metric(self) -> None:
        flow = self._load(self.source)
        metric = flow.steps[1]
        self.assertEqual(metric.id, "groups")
        self.assertEqual(metric.depends_on, ["classify"])
        relation = metric.metric_calculation.reducer.relation
        self.assertEqual(relation.operator.value, "intersects")
        self.assertEqual(relation.left.value, "left.resources")
        self.assertEqual(relation.right.value, "right.resources")

    def test_rejects_object_item_as_relation_operand(self) -> None:
        source = self.source.replace('"{{left.resources}}"', '"{{left}}"')
        with self.assertRaisesRegex(FlowValidationError, "relation.left.*array"):
            self._load(source)

    def test_rejects_invalid_relation_declarations(self) -> None:
        replacements = [
            ("operator: intersects", "operator: equals", "operator"),
            ("left.resources", "item.resources", "relation.left.*left"),
            ("right.resources", "params.resources", "relation.right.*right"),
            ("left.resources", "left.missing", "missing.*not declared"),
            ("right.resources", "right.name", "relation.right.*array"),
            ("items: {type: string}", "items: {type: object}", "scalar"),
            ("value: {type: integer, minimum: 0}", "value: {type: number}", "integer"),
            (
                "operator: intersects",
                "operator: intersects\n              unexpected: true",
                "unexpected",
            ),
            (
                "type: component_count",
                'type: component_count\n            value: "{{item}}"',
                r"component_count\.value\s+Extra inputs are not permitted",
            ),
        ]
        for original, replacement, diagnostic in replacements:
            with (
                self.subTest(replacement=replacement),
                self.assertRaisesRegex(FlowValidationError, diagnostic),
            ):
                self._load(self.source.replace(original, replacement))

    def test_rejects_missing_relation(self) -> None:
        start = self.source.index("            relation:\n")
        end = self.source.index("          severe:", start)
        with self.assertRaisesRegex(FlowValidationError, "relation"):
            self._load(self.source[:start] + self.source[end:])

    def _load(self, source: str):
        self.path.write_text(source, encoding="utf-8")
        return self.assembly.flow_loader.load(str(self.path), [])
