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

from harness.output_spec_factory import OutputSpecFactory
from harness.step_declaration_factory import StepDeclarationFactory


class TestStepDeclarationFactory(unittest.TestCase):
    def setUp(self):
        self.sut = StepDeclarationFactory(OutputSpecFactory())

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
