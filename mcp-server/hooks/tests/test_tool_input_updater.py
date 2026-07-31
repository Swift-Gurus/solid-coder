"""
solid-name: test_tool_input_updater
solid-category: unit-test
solid-description: Tests ToolInputUpdater's per-tool schema for building an updated tool_input after content correction.
"""

import unittest

from _path_bootstrap import ensure_on_path  # noqa: E402, F401

from tool_input_updater import ToolInputUpdater


class TestToolInputUpdater(unittest.TestCase):
    def setUp(self):
        self.updater = ToolInputUpdater()

    def test_write_tool_sets_content(self):
        result = self.updater.build("Write", {"file_path": "/tmp/x", "content": "old"}, "new", "")

        self.assertEqual(result["content"], "new")
        self.assertEqual(result["file_path"], "/tmp/x")

    def test_edit_tool_with_existing_sets_old_and_new_string_and_drops_replace_all(self):
        result = self.updater.build(
            "Edit",
            {"file_path": "/tmp/x", "old_string": "a", "new_string": "b", "replace_all": True},
            "corrected",
            "existing text",
        )

        self.assertEqual(result["old_string"], "existing text")
        self.assertEqual(result["new_string"], "corrected")
        self.assertNotIn("replace_all", result)

    def test_edit_tool_without_existing_sets_only_new_string(self):
        result = self.updater.build("Edit", {"file_path": "/tmp/x", "new_string": "b"}, "corrected", "")

        self.assertEqual(result["new_string"], "corrected")
        self.assertNotIn("old_string", result)

    def test_does_not_mutate_the_original_tool_input(self):
        original = {"file_path": "/tmp/x", "content": "old"}

        self.updater.build("Write", original, "new", "")

        self.assertEqual(original["content"], "old")


if __name__ == "__main__":
    unittest.main()
