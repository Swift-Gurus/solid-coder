"""Tests for hooks/enforce_full_reference_read.py.

Contract:
  - Exit 0 (allow) for non-reference files regardless of offset/limit
  - Exit 0 (allow) for reference files with no offset/limit
  - Exit 2 (block) for reference files with offset set
  - Exit 2 (block) for reference files with limit set
  - Exit 2 (block) for reference files with both set
  - Stderr contains the file path and reason on block
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOOK = PROJECT_ROOT / "hooks" / "enforce_full_reference_read.py"
REFS_ROOT = PROJECT_ROOT / "references"


def run(tool_name, file_path, offset=None, limit=None):
    tool_input = {"file_path": str(file_path)}
    if offset is not None:
        tool_input["offset"] = offset
    if limit is not None:
        tool_input["limit"] = limit
    event = {"tool_name": tool_name, "tool_input": tool_input}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True, text=True,
    )


REF_FILE = REFS_ROOT / "principles" / "SRP" / "rule.md"
OTHER_FILE = PROJECT_ROOT / "mcp-server" / "server.py"


class TestNonReferenceFiles(unittest.TestCase):
    def test_allows_non_reference_with_no_limit(self):
        r = run("Read", OTHER_FILE)
        self.assertEqual(r.returncode, 0)

    def test_allows_non_reference_with_offset(self):
        r = run("Read", OTHER_FILE, offset=10)
        self.assertEqual(r.returncode, 0)

    def test_allows_non_reference_with_limit(self):
        r = run("Read", OTHER_FILE, limit=50)
        self.assertEqual(r.returncode, 0)


class TestReferenceFiles(unittest.TestCase):
    def test_allows_full_read(self):
        r = run("Read", REF_FILE)
        self.assertEqual(r.returncode, 0)

    def test_blocks_offset(self):
        r = run("Read", REF_FILE, offset=5)
        self.assertEqual(r.returncode, 2)
        self.assertIn(str(REF_FILE), r.stderr)
        self.assertIn("offset=5", r.stderr)

    def test_blocks_limit(self):
        r = run("Read", REF_FILE, limit=100)
        self.assertEqual(r.returncode, 2)
        self.assertIn("limit=100", r.stderr)

    def test_blocks_both(self):
        r = run("Read", REF_FILE, offset=10, limit=20)
        self.assertEqual(r.returncode, 2)
        self.assertIn("offset=10", r.stderr)
        self.assertIn("limit=20", r.stderr)

    def test_stderr_mentions_full_file_requirement(self):
        r = run("Read", REF_FILE, limit=50)
        self.assertIn("full file", r.stderr.lower())


class TestNonReadTool(unittest.TestCase):
    def test_ignores_non_read_tool(self):
        r = run("Write", REF_FILE, offset=5)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
