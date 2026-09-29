"""Validates rejected co-located metric authoring forms."""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_validation_error import FlowValidationError


"""
solid-name: TestCoLocatedMetricValidation
solid-category: unit-test
solid-spec: [SPEC-058]
solid-description: Verifies compact metric syntax rejects ambiguous sources and independent scheduling fields.
"""
class TestCoLocatedMetricValidation(unittest.TestCase):
    def setUp(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)
        self.loader = FlowEngineAssemblyFactory().build().flow_loader

    def test_rejects_missing_local_output(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "metric 'count' on step 'classify'.*missing",
        ):
            self._load(self._workflow(source="missing"))

    def test_rejects_cross_step_source_expression(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "explicit 'type: metric' step",
        ):
            self._load(
                self._workflow(
                    source="{{steps.other.outputs.observations}}",
                )
            )

    def test_rejects_non_data_output(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "must reference a data output",
        ):
            self._load(
                self._workflow(
                    source="observations",
                    output_type="file",
                )
            )

    def test_rejects_independent_scheduling_fields(self) -> None:
        source = self._workflow(source="observations").replace(
            "\n        metric_id: TEST-1\n",
            "\n        metric_id: TEST-1\n"
            "        depends_on: [other]\n",
        )

        with self.assertRaisesRegex(FlowValidationError, "depends_on"):
            self._load(source)

    def test_rejects_duplicate_runtime_step_id(self) -> None:
        source = self._workflow(source="observations").replace(
            "id: count",
            "id: classify_exception",
        ).replace(
            "depends_on: [count]",
            "depends_on: [classify_exception]",
        )

        with self.assertRaisesRegex(FlowValidationError, "Duplicate step ID"):
            self._load(source)

    def test_rejects_owner_level_for_each_until_instance_local_contract(self) -> None:
        source = self._workflow(source="observations").replace(
            "steps:\n  - id: classify\n",
            "steps:\n"
            "  - id: prepare\n"
            "    prompt: Prepare units.\n"
            "    outputs:\n"
            "      - name: units\n"
            "        type: data\n"
            "        schema: {type: array, items: {type: string}}\n"
            "  - id: classify\n",
        ).replace(
            "    prompt: Classify observations.\n",
            "    prompt: Classify observations.\n"
            "    depends_on: [prepare]\n"
            '    for_each: "{{steps.prepare.outputs.units}}"\n',
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "with for_each must use explicit metric steps",
        ):
            self._load(source)

    def test_rejects_non_agent_owner(self) -> None:
        source = self._workflow(source="observations").replace(
            "    prompt: Classify observations.\n",
            "    type: command\n"
            "    command: echo observations\n",
        )

        with self.assertRaisesRegex(
            FlowValidationError,
            "must be type 'agent' to declare metrics",
        ):
            self._load(source)

    def _load(self, source: str) -> None:
        path = self.directory / "workflow.yaml"
        path.write_text(source, encoding="utf-8")
        self.loader.load(str(path), [])

    @staticmethod
    def _workflow(source: str, output_type: str = "data") -> str:
        return textwrap.dedent(
            f"""
            id: compact-metric-validation
            name: Compact Metric Validation
            max_turns: 3
            rule: {{}}
            steps:
              - id: classify
                prompt: Classify observations.
                outputs:
                  - name: observations
                    type: {output_type}
                    schema:
                      type: array
                      items: {{type: string}}
                metrics:
                  - id: count
                    metric_id: TEST-1
                    value: {{type: integer, minimum: 0}}
                    scoring:
                      source: '{source}'
                      severe: {{operator: greater_than, value: 1}}
              - id: classify_exception
                type: exception
                depends_on: [count]
                prompt: Classify the rule exception.
            """
        )


if __name__ == "__main__":
    unittest.main()
