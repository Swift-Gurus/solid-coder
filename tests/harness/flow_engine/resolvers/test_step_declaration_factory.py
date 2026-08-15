"""
solid-name: test_step_declaration_factory
solid-category: unit-test
solid-spec: [SPEC-027, SPEC-035]
solid-description: Tests mapping structured workflow input into typed step declarations.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.comparison_condition_parser import ComparisonConditionParser
from harness.composition_condition_parser import CompositionConditionParser
from harness.condition_operator import ConditionOperator
from harness.condition_parser import ConditionParser
from harness.step_declaration_factory import StepDeclarationFactory


class TestStepDeclarationFactory(unittest.TestCase):
    def setUp(self):
        self.sut = StepDeclarationFactory(
            condition_parser=ConditionParser(
                composition_parser=CompositionConditionParser(),
                comparison_parser=ComparisonConditionParser(),
            )
        )

    def test_maps_when_to_a_typed_condition_declaration(self):
        declaration = self.sut.map(
            {
                "id": "review",
                "prompt": "Review",
                "when": {
                    "ref": "{{item.language}}",
                    "equals": "swift",
                },
            }
        )

        self.assertEqual(
            declaration.condition,
            ComparisonCondition(
                reference="{{item.language}}",
                operator=ConditionOperator.EQUALS,
                expected="swift",
            ),
        )

    def test_maps_process_fields_to_named_attributes(self):
        declaration = self.sut.map(
            {
                "id": "validate",
                "type": "script",
                "script_file": "/package/scripts/validate.py",
                "executor": "python3",
                "args": ["--strict"],
                "timeout_seconds": 30,
                "max_attempts": 2,
            }
        )

        self.assertEqual(declaration.id, "validate")
        self.assertEqual(declaration.type, "script")
        self.assertEqual(declaration.script_file, "/package/scripts/validate.py")
        self.assertEqual(declaration.executor, "python3")
        self.assertEqual(declaration.args, ["--strict"])
        self.assertEqual(declaration.timeout_seconds, 30)
        self.assertEqual(declaration.max_attempts, 2)

    def test_maps_output_mappings_to_output_spec_objects(self):
        declaration = self.sut.map(
            {
                "id": "review",
                "prompt": "Review",
                "outputs": [
                    {
                        "name": "findings",
                        "type": "data",
                        "schema": {"type": "array"},
                    }
                ],
            }
        )

        self.assertEqual(len(declaration.outputs), 1)
        self.assertEqual(declaration.outputs[0].name, "findings")
        self.assertEqual(declaration.outputs[0].schema, {"type": "array"})


if __name__ == "__main__":
    unittest.main()
