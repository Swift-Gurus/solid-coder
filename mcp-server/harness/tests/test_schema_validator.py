"""
solid-name: TestSchemaValidator
solid-description: Verifies correct validation behavior for typed outputs with optional schemas and file path checks.
solid-category: unit-test
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from harness.flow_engine_assembly import build_default_assembly
from harness.models import OutputSpec


class TestSchemaValidator(unittest.TestCase):

    def setUp(self):
        self.validator = build_default_assembly().schema_validator

    def test_data_with_no_schema_passes(self):
        spec = OutputSpec(name="out", type="data")
        result = self.validator.validate(spec, {"key": "value"})
        self.assertTrue(result.ok)

    def test_data_with_inline_schema_valid_value(self):
        spec = OutputSpec(name="out", type="data", schema={"type": "array", "items": {"type": "string"}})
        result = self.validator.validate(spec, ["SRP", "OCP"])
        self.assertTrue(result.ok)

    def test_data_with_inline_schema_invalid_value(self):
        spec = OutputSpec(name="out", type="data", schema={"type": "array", "items": {"type": "string"}})
        result = self.validator.validate(spec, "not_a_list")
        self.assertFalse(result.ok)
        self.assertTrue(len(result.errors) > 0)

    def test_file_type_existing_path(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        spec = OutputSpec(name="out", type="file")
        result = self.validator.validate(spec, path)
        self.assertTrue(result.ok)

    def test_file_type_missing_path(self):
        spec = OutputSpec(name="out", type="file")
        result = self.validator.validate(spec, "/nonexistent/path/file.json")
        self.assertFalse(result.ok)

    def test_unknown_output_type_returns_error(self):
        spec = OutputSpec(name="out", type="unknown_type")
        result = self.validator.validate(spec, "anything")
        self.assertFalse(result.ok)
        self.assertIn("Unknown output type", result.errors[0])


if __name__ == "__main__":
    unittest.main()
