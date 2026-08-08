"""Tests for pre_write_gate.py — unsupported extensions skip the health check entirely."""

import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from _gate_fixtures import HC, PYTHON_CONTENT, call_main, event


class TestGateFileTypeRouting(unittest.TestCase):
    def test_kt_file_skips_run_health(self):
        with patch(HC) as hc:
            code, out = call_main(event("Write", "/src/Foo.kt", PYTHON_CONTENT))
        hc.assert_not_called()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
