"""
solid-name: TestSafeYamlParser
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies YAML boundary failures use the shared validation error contract.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.yaml_support import SafeYamlParser


class TestSafeYamlParser(unittest.TestCase):
    def test_malformed_yaml_uses_validation_error(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "Malformed YAML"):
            SafeYamlParser().parse("name: [broken")

    def test_empty_document_remains_an_empty_mapping(self) -> None:
        self.assertEqual(SafeYamlParser().parse(""), {})

    def test_valid_yaml_preserves_parsed_values(self) -> None:
        self.assertEqual(SafeYamlParser().parse("name: Target"), {"name": "Target"})
