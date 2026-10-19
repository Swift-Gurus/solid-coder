"""Checks exact conversion between UTF-8 source offsets and UTF-16 positions."""

import unittest

from source.analysis.provenance.semantic_position import SemanticPosition
from source.analysis.provenance.utf16_source_position_resolver import UTF16SourcePositionResolver
from source.analysis.provenance.utf8_semantic_offset_resolver import UTF8SemanticOffsetResolver


class TestUTF16SourcePositionConverter(unittest.TestCase):
    def setUp(self):
        self.positions = UTF16SourcePositionResolver()
        self.offsets = UTF8SemanticOffsetResolver()

    def test_unicode_round_trip(self):
        source = "first\nlet 🧪 = café; service\n"
        offset = source.encode().index(b"service")
        position = self.positions.resolve(source, offset)
        self.assertEqual(position, SemanticPosition(line=1, character=15))
        self.assertEqual(self.offsets.resolve(source, position), offset)

    def test_empty_final_line_and_crlf_round_trip(self):
        for source in ["", "a\n", "a\r\nb\r\n"]:
            offset = len(source.encode())
            self.assertEqual(self.offsets.resolve(source, self.positions.resolve(source, offset)), offset)

    def test_position_cannot_split_a_surrogate_pair(self):
        with self.assertRaises(ValueError):
            self.offsets.resolve("🧪", SemanticPosition(line=0, character=1))

    def test_byte_offset_cannot_split_utf8_character(self):
        with self.assertRaises(ValueError):
            self.positions.resolve("🧪", 1)

    def test_out_of_range_coordinates_are_rejected(self):
        for position in [SemanticPosition(line=2, character=0), SemanticPosition(line=0, character=10)]:
            with self.assertRaises(ValueError):
                self.offsets.resolve("text", position)
        for offset in [-1, 20]:
            with self.assertRaises(ValueError):
                self.positions.resolve("text", offset)
