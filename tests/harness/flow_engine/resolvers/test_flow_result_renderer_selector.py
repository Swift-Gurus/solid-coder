"""
solid-name: test_flow_result_renderer_selector
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests selecting between the plain-text and full-JSON flow result renderers.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_result_renderer_selector import FlowResultRendererSelector


class StubRenderer:
    pass


class TestFlowResultRendererSelector(unittest.TestCase):

    def setUp(self):
        self.plain_text_renderer = StubRenderer()
        self.json_renderer = StubRenderer()
        self.sut = FlowResultRendererSelector(
            plain_text_renderer=self.plain_text_renderer,
            json_renderer=self.json_renderer,
        )

    def test_selects_the_plain_text_renderer_when_flag_is_true(self):
        self.assertIs(self.sut.select(True), self.plain_text_renderer)

    def test_selects_the_json_renderer_when_flag_is_false(self):
        self.assertIs(self.sut.select(False), self.json_renderer)


if __name__ == "__main__":
    unittest.main()
