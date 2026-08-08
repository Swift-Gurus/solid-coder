"""
solid-name: test_schema_resolver
solid-category: unit-test
solid-spec: [SPEC-030]
solid-description: Tests resolving a JSON Schema from an OutputSpec's inline schema field.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import OutputSpec
from harness.schema_resolving import SchemaResolver


class TestSchemaResolver(unittest.TestCase):

    def test_returns_the_inline_schema_when_present(self):
        sut = SchemaResolver()
        spec = OutputSpec(name="greeting", type="data", schema={"type": "string"})

        self.assertEqual(sut.resolve(spec), {"type": "string"})

    def test_returns_none_when_no_schema_declared(self):
        sut = SchemaResolver()
        spec = OutputSpec(name="greeting", type="data")

        self.assertIsNone(sut.resolve(spec))


if __name__ == "__main__":
    unittest.main()
