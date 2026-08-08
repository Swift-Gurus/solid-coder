"""Tests for the corrected_content extraction path via hook_utils.parse_json_field."""

import json
import sys
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks")
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from _frontmatter_fixtures import CLEAN_CONTENT


class TestParseCorrectedContent(unittest.TestCase):
    def _parse(self, raw):
        from hook_utils import parse_json_field, StrValidator
        v = parse_json_field(raw, "corrected_content", StrValidator())
        return v if v is not None else None

    def test_extracts_corrected_content_from_plain_json(self):
        raw = json.dumps({"corrected_content": CLEAN_CONTENT})
        self.assertEqual(self._parse(raw), CLEAN_CONTENT)

    def test_extracts_corrected_content_with_code_fence(self):
        raw = "\n" + json.dumps({"corrected_content": CLEAN_CONTENT}) + "\n"
        self.assertEqual(self._parse(raw), CLEAN_CONTENT)

    def test_extracts_corrected_content_with_surrounding_text(self):
        raw = "Here is the result:\n" + json.dumps({"corrected_content": CLEAN_CONTENT}) + "\nDone."
        self.assertEqual(self._parse(raw), CLEAN_CONTENT)

    def test_returns_none_for_missing_field(self):
        self.assertIsNone(self._parse(json.dumps({"other_field": "value"})))

    def test_returns_none_for_invalid_json(self):
        self.assertIsNone(self._parse("not json at all"))

    def test_returns_none_for_empty_string(self):
        self.assertIsNone(self._parse(""))

    def test_returns_none_when_corrected_content_is_not_string(self):
        self.assertIsNone(self._parse(json.dumps({"corrected_content": 42})))


if __name__ == "__main__":
    unittest.main()
