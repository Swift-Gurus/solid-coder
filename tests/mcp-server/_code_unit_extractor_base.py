"""
solid-description: Provides shared test infrastructure for validating code extraction across programming languages.
solid-category: unit-test
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp-server"))
from health.code_unit_extractor import CodeUnitExtractor


class CodeUnitExtractorTestBase:
    """Mixin providing shared setUp, _x helper, and language-agnostic tests.

    Subclasses must define ``language`` and inherit from both this class
    and ``unittest.TestCase`` (in that MRO order).
    """

    language: str = ""

    def setUp(self):
        self._e = CodeUnitExtractor()

    def _x(self, code: str) -> list:
        return self._e.extract(code, self.language)

    def test_empty_file_returns_empty(self):
        self.assertEqual([], self._x(""))