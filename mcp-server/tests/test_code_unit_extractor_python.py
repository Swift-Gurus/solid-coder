"""
solid-name: TestCodeUnitExtractorPython
solid-category: unit-test
solid-description: Validates code unit extraction for Python source.
"""

import unittest

from _code_unit_extractor_base import CodeUnitExtractorTestBase


class TestCodeUnitExtractorPython(CodeUnitExtractorTestBase, unittest.TestCase):
    language = "Python"

    def test_class_detected(self):
        self.assertIn("MyClass", self._x("class MyClass:\n    pass"))

    def test_function_detected(self):
        self.assertIn("my_func", self._x("def my_func():\n    pass"))

    def test_multiple_units(self):
        units = self._x("class A:\n    pass\ndef b():\n    pass")
        self.assertIn("A", units)
        self.assertIn("b", units)


if __name__ == "__main__":
    unittest.main()
