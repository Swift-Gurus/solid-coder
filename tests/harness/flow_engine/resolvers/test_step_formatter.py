"""
solid-name: test_step_formatter
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests formatting a step's header and body into the text the calling agent sees.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.step_formatter import StepFormatter


class TestStepFormatter(unittest.TestCase):

    def setUp(self):
        self.sut = StepFormatter()

    def test_formats_the_instance_id_header_and_body(self):
        result = self.sut.format("a-1", "Do the thing.", None)

        self.assertEqual(result, "id: a-1\n\nDo the thing.")

    def test_includes_the_rejection_reason_in_the_header_when_set(self):
        result = self.sut.format("a-1", "Do the thing.", "12345 is not of type 'string'")

        self.assertEqual(
            result,
            "id: a-1\nRejected: 12345 is not of type 'string'. Try again.\n\nDo the thing.",
        )


if __name__ == "__main__":
    unittest.main()
