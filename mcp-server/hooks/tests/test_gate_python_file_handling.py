"""Tests for pre_write_gate.py — Python files go through the same health/frontmatter checks."""

import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from _gate_fixtures import FM, HC, PYTHON_CONTENT, SRP_VIOLATION_WITH_METRIC, VIOLATIONS, call_main, event
from test_utils import parse_hook_output


class TestGatePythonFileHandling(unittest.TestCase):
    def test_py_file_invokes_run_health(self):
        with patch(FM, return_value=PYTHON_CONTENT), patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Foo.py", PYTHON_CONTENT))
        hc.assert_called_once()

    def test_py_file_clean_allows(self):
        with patch(FM, return_value=PYTHON_CONTENT), patch(HC, return_value=[]):
            code, out = call_main(event("Write", "/src/Foo.py", PYTHON_CONTENT))
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_py_file_violation_denies(self):
        with patch(FM, return_value=PYTHON_CONTENT), patch(HC, return_value=VIOLATIONS):
            code, out = call_main(event("Write", "/src/Foo.py", PYTHON_CONTENT))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("SRP", h["permissionDecisionReason"])

    def test_py_violation_with_metric_id_denies_with_issue_in_reason(self):
        with patch(FM, return_value=PYTHON_CONTENT), patch(HC, return_value=SRP_VIOLATION_WITH_METRIC):
            code, out = call_main(event("Write", "/src/Foo.py", PYTHON_CONTENT))
        h = parse_hook_output(out)
        self.assertEqual(h["permissionDecision"], "deny")
        self.assertIn("SRP", h["permissionDecisionReason"])
        self.assertIn("Multiple responsibilities", h["permissionDecisionReason"])


if __name__ == "__main__":
    unittest.main()
