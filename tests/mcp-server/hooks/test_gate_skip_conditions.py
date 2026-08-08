"""Tests for pre_write_gate.py — conditions under which checks are skipped entirely."""

import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from _gate_fixtures import FM, HC, LONG_SWIFT, SHORT_SWIFT, call_main, event
from solid_coder_config import SolidCoderConfig


class TestGateSkipConditions(unittest.TestCase):
    def setUp(self):
        patcher = patch("hc_config.load_config", return_value=SolidCoderConfig(code_review_on_write_enabled=True))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_non_swift_allows_without_checks(self):
        with patch(HC) as hc, patch(FM) as fm:
            code, out = call_main(event("Write", "/src/Foo.kt", LONG_SWIFT))
        fm.assert_not_called()
        hc.assert_not_called()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_new_swift_file_runs_health_check(self):
        """Health check always runs for new .swift files regardless of size."""
        with patch(FM, return_value=SHORT_SWIFT), patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/Foo.swift", SHORT_SWIFT))
        hc.assert_called_once()

    def test_test_file_runs_health_check(self):
        """Test files are no longer excluded — unit testing rules apply."""
        with patch(FM, return_value=LONG_SWIFT), patch(HC, return_value=[]) as hc:
            call_main(event("Write", "/src/FooTests.swift", LONG_SWIFT))
        hc.assert_called_once()

    def test_read_tool_allows_immediately(self):
        with patch(FM) as fm:
            code, _ = call_main({"tool_name": "Read", "tool_input": {"file_path": "/src/Foo.swift"}, "session_id": "s"})
        fm.assert_not_called()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
