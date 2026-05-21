"""solid-description: Verifies that fix-instructions retrieval correctly serves guidance for recognised metric identifiers and reports failure for unrecognised ones.
solid-category: unit-test
"""

import unittest
from tests.helpers import make_handler


class TestLoadFixInstructions(unittest.TestCase):
    def setUp(self):
        self.handler = make_handler()

    def test_known_metric_id_returns_nonempty_text(self):
        result = self.handler.load_fix_instructions("SRP-1")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_known_metric_id_result_has_no_yaml_frontmatter(self):
        result = self.handler.load_fix_instructions("SRP-1")
        self.assertFalse(result.startswith("---"), "Result must not start with YAML frontmatter delimiter")

    def test_known_metric_id_result_contains_metric_id_in_header(self):
        result = self.handler.load_fix_instructions("SRP-1")
        self.assertIn("SRP-1", result)

    def test_unknown_metric_id_returns_error_string(self):
        result = self.handler.load_fix_instructions("UNKNOWN-99")
        self.assertIsInstance(result, str)
        self.assertIn("UNKNOWN-99", result)

    def test_unknown_metric_id_result_does_not_start_with_hash(self):
        result = self.handler.load_fix_instructions("UNKNOWN-99")
        self.assertFalse(result.startswith("# "), "Error response must not start with a markdown header")


if __name__ == "__main__":
    unittest.main()