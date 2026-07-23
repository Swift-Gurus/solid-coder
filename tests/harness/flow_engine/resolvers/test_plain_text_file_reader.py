"""
solid-name: test_plain_text_file_reader
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests reading plain text files by path, and returning None instead of raising when the path does not resolve.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from utils.prompt_builder import PlainTextFileReader


class TestPlainTextFileReader(unittest.TestCase):

    def setUp(self):
        self.reader = PlainTextFileReader()

    def test_reads_existing_file_contents(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name

        self.assertEqual(self.reader.read(Path(path)), "hello world")

    def test_returns_none_for_missing_path(self):
        self.assertIsNone(self.reader.read(Path("/nonexistent/path/prompt.md")))


if __name__ == "__main__":
    unittest.main()
