"""Tests for low-risk edit detection in pre_write_gate.py"""

import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = str(Path(__file__).resolve().parents[1])
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from pre_write_gate import EditClassifier, _diff_chunks


class TestIsFrontmatterOnly(unittest.TestCase):
    def setUp(self):
        self.c = EditClassifier()

    def test_detects_frontmatter_only_change(self):
        old = "/**\n solid-name: Foo\n solid-category: service\n solid-description: Old.\n */"
        new = "/**\n solid-name: Foo\n solid-category: service\n solid-description: New.\n */"
        self.assertTrue(self.c.is_frontmatter_only(old, new))

    def test_rejects_when_code_present(self):
        old = "/**\n solid-name: Foo\n solid-description: Old.\n */\nfinal class Foo {}"
        new = "/**\n solid-name: Foo\n solid-description: New.\n */\nfinal class Foo {}"
        self.assertFalse(self.c.is_frontmatter_only(old, new))


class TestIsReorder(unittest.TestCase):
    def setUp(self):
        self.c = EditClassifier()

    def test_detects_argument_reorder(self):
        self.assertTrue(self.c.is_reorder(
            "func foo(a: Int, b: String)",
            "func foo(b: String, a: Int)",
        ))

    def test_detects_import_reorder(self):
        self.assertTrue(self.c.is_reorder(
            "import Foundation\nimport SwiftUI",
            "import SwiftUI\nimport Foundation",
        ))

    def test_rejects_new_parameter(self):
        self.assertFalse(self.c.is_reorder(
            "func foo(a: Int)",
            "func foo(a: Int, b: String)",
        ))

    def test_rejects_new_function(self):
        self.assertFalse(self.c.is_reorder(
            "func foo() {}",
            "func foo() {}\nfunc bar() {}",
        ))


class TestIsRename(unittest.TestCase):
    def setUp(self):
        self.c = EditClassifier()

    def test_detects_function_rename(self):
        self.assertTrue(self.c.is_rename(
            "func oldName(a: Int) -> Bool",
            "func newName(a: Int) -> Bool",
        ))

    def test_detects_variable_rename(self):
        self.assertTrue(self.c.is_rename("let myVar = 42", "let renamedVar = 42"))

    def test_rejects_structural_change(self):
        self.assertFalse(self.c.is_rename(
            "func foo(a: Int)",
            "func foo(a: Int, b: String)",
        ))


class TestDiffChunks(unittest.TestCase):
    def test_extracts_changed_lines_only(self):
        old = "line1\nline2\nline3"
        new = "line1\nLINE2_CHANGED\nline3"
        old_chunk, new_chunk = _diff_chunks(old, new)
        self.assertEqual(old_chunk, "line2")
        self.assertEqual(new_chunk, "LINE2_CHANGED")

    def test_identical_content_returns_empty(self):
        content = "func foo() {}"
        old_chunk, new_chunk = _diff_chunks(content, content)
        self.assertEqual(old_chunk, "")
        self.assertEqual(new_chunk, "")

    def test_new_file_returns_all_as_new(self):
        old_chunk, new_chunk = _diff_chunks("", "func foo() {}")
        self.assertEqual(new_chunk, "func foo() {}")


class TestIsLowRiskEdit(unittest.TestCase):
    def setUp(self):
        self.c = EditClassifier()

    def test_frontmatter_change_is_low_risk(self):
        old = "/**\n solid-name: Foo\n solid-description: Old.\n */"
        new = "/**\n solid-name: Foo\n solid-description: New.\n */"
        self.assertTrue(self.c.is_low_risk(old, new))

    def test_reorder_is_low_risk(self):
        self.assertTrue(self.c.is_low_risk(
            "func foo(a: Int, b: String)",
            "func foo(b: String, a: Int)",
        ))

    def test_rename_is_low_risk(self):
        self.assertTrue(self.c.is_low_risk(
            "func oldName(a: Int) -> Bool",
            "func newName(a: Int) -> Bool",
        ))

    def test_new_logic_is_not_low_risk(self):
        self.assertFalse(self.c.is_low_risk(
            "func foo() { return 1 }",
            "func foo() { return 1 }\nfunc bar() { return 2 }",
        ))


class TestWriteDiffIntegration(unittest.TestCase):
    """Verify that Write with an existing file uses diff-based low-risk detection."""

    def setUp(self):
        self.c = EditClassifier()

    def _make_file(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".swift", delete=False)
        f.write(content)
        f.close()
        return f.name

    def test_rename_write_is_low_risk(self):
        original = "func oldName(a: Int) -> Bool { return true }\n"
        updated  = "func newName(a: Int) -> Bool { return true }\n"
        old_chunk, new_chunk = _diff_chunks(original, updated)
        self.assertTrue(self.c.is_low_risk(old_chunk, new_chunk))

    def test_new_method_write_is_not_low_risk(self):
        original = "func foo() {}\n"
        updated  = "func foo() {}\nfunc bar() { doSomethingNew() }\n"
        old_chunk, new_chunk = _diff_chunks(original, updated)
        self.assertFalse(self.c.is_low_risk(old_chunk, new_chunk))

    def test_new_file_has_no_diff(self):
        """New file — OSError on read → low_risk stays False → full health check."""
        old_chunk, new_chunk = _diff_chunks("", "func foo() {}")
        self.assertFalse(self.c.is_low_risk(old_chunk, new_chunk))


if __name__ == "__main__":
    unittest.main()
