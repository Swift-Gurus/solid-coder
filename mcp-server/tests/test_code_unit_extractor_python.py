"""
solid-name: TestCodeUnitExtractorPython
solid-category: unit-test
solid-description: Validates code unit extraction for Python source.
"""

import unittest
from health.code_unit_extractor import CodeUnitExtractor


class TestCodeUnitExtractorPython(unittest.TestCase):
    def setUp(self):
        self._e = CodeUnitExtractor()

    def test_class_detected(self):
        self.assertIn("MyClass", self._e.extract("class MyClass:\n    pass", "Python"))

    def test_function_detected(self):
        self.assertIn("my_func", self._e.extract("def my_func():\n    pass", "Python"))

    def test_multiple_units(self):
        units = self._e.extract("class A:\n    pass\ndef b():\n    pass", "Python")
        self.assertIn("A", units)
        self.assertIn("b", units)

    def test_empty_file_returns_empty(self):
        self.assertEqual([], self._e.extract("", "Python"))


if __name__ == "__main__":
    unittest.main()
