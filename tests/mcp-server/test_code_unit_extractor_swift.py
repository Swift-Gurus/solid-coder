"""
solid-name: TestCodeUnitExtractorSwift
solid-category: unit-test
solid-description: Verifies extraction of Swift code unit names.
"""

import unittest

from _code_unit_extractor_base import CodeUnitExtractorTestBase


class TestCodeUnitExtractorSwift(CodeUnitExtractorTestBase, unittest.TestCase):
    language = "Swift"

    def test_class_detected(self):
        self.assertIn("Foo", self._x("class Foo {}"))

    def test_struct_detected(self):
        self.assertIn("Bar", self._x("struct Bar {}"))

    def test_protocol_detected(self):
        self.assertIn("MyProtocol", self._x("protocol MyProtocol {}"))

    def test_enum_detected(self):
        self.assertIn("Status", self._x("enum Status { case a }"))

    def test_actor_detected(self):
        self.assertIn("MyActor", self._x("actor MyActor {}"))

    def test_extension_detected(self):
        self.assertIn("String", self._x("extension String { func foo() {} }"))

    def test_public_modifier_handled(self):
        self.assertIn("Foo", self._x("public class Foo {}"))

    def test_final_modifier_handled(self):
        self.assertIn("Bar", self._x("final class Bar {}"))

    def test_multiple_declarations_all_returned(self):
        code = "class Foo {}\nstruct Bar {}\nenum Baz {}"
        units = self._x(code)
        self.assertIn("Foo", units)
        self.assertIn("Bar", units)
        self.assertIn("Baz", units)

    def test_deduplicated_when_name_repeated(self):
        code = "class Foo {}\nextension Foo {}"
        self.assertEqual(self._x(code).count("Foo"), 1)


if __name__ == "__main__":
    unittest.main()
