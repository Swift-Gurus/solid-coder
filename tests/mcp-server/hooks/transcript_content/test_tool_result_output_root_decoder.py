"""Tests typed output-root decoding from host tool results."""

import json
import unittest

from transcript_content.tool_result_output_root_decoder import ToolResultOutputRootDecoder


"""
solid-name: TestToolResultOutputRootDecoder
solid-category: unit-test
solid-description: Verifies text and block-based tool results yield only valid output locations without inspecting runtime payload types.
"""
class TestToolResultOutputRootDecoder(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = ToolResultOutputRootDecoder()

    def test_plain_text_json_returns_the_output_root(self) -> None:
        self.assertEqual(self.sut.decode(json.dumps({"output_root": "/project/output"}), "tool result"), "/project/output")

    def test_text_block_after_nontext_block_returns_the_output_root(self) -> None:
        content = [{"type": "image"}, {"type": "text", "text": json.dumps({"output_root": "/project/output"})}]
        self.assertEqual(self.sut.decode(content, "tool result"), "/project/output")

    def test_later_plain_text_does_not_invalidate_the_first_text_block(self) -> None:
        content = [{"type": "text", "text": json.dumps({"output_root": "/project/output"})}, {"type": "text", "text": "details"}]
        self.assertEqual(self.sut.decode(content, "tool result"), "/project/output")

    def test_missing_output_root_returns_no_location(self) -> None:
        self.assertEqual(self.sut.decode('{"other": "value"}', "tool result"), "")

    def test_malformed_json_returns_no_location(self) -> None:
        self.assertEqual(self.sut.decode("not json", "tool result"), "")

    def test_empty_content_returns_no_location(self) -> None:
        self.assertEqual(self.sut.decode("", "tool result"), "")

    def test_nonstrings_cannot_become_output_locations(self) -> None:
        self.assertEqual(self.sut.decode('{"output_root": 42}', "tool result"), "")
