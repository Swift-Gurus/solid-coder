"""Tests for hooks/validate_json_schema.py.

Contract:
  - Silent (exit 0, no stdout) for valid known JSON files
  - Outputs JSON {hookSpecificOutput: {userFacingError: ...}} and exits 1 for invalid files
  - Silent for JSON files with no registered schema
  - Silent for non-JSON files
  - Silent for non-Write/Edit tool events
  - Graceful on malformed event JSON
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOOK = PROJECT_ROOT / "hooks" / "validate_json_schema.py"
FAKE_PROJECT = "/tmp/test-project"

VALID_ARCH = {
    "spec_summary": "Build a login screen",
    "components": [],
    "wiring": [],
    "composition_root": "LoginFactory",
}

INVALID_ARCH = {
    "components": [],
    # missing spec_summary, wiring, composition_root
}

VALID_OUTPUT = {
    "file_path": "/path/to/Foo.swift",
    "timestamp": "2026-01-01T00:00:00Z",
    "principles": [],
}

INVALID_OUTPUT = {
    "file_path": "/path/to/Foo.swift",
    # missing timestamp and principles
}


def run(tool_name, file_path, content, project_dir=FAKE_PROJECT):
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path), "content": content},
        "tool_response": {"type": "result", "content": "File written."},
    }
    env = {
        **os.environ,
        "CLAUDE_PLUGIN_ROOT": str(PROJECT_ROOT),
        "CLAUDE_PROJECT_DIR": project_dir,
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True, text=True, env=env,
    )


def write_tmp(data, suffix=".json"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    json.dump(data, f)
    f.close()
    return Path(f.name)


class TestKnownFiles(unittest.TestCase):
    def test_valid_arch_json_silent(self):
        tmp = write_tmp(VALID_ARCH)
        tmp.rename(tmp.parent / "arch.json")
        path = tmp.parent / "arch.json"
        try:
            r = run("Write", path, json.dumps(VALID_ARCH))
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "")
        finally:
            path.unlink(missing_ok=True)

    def test_invalid_arch_json_reports_errors(self):
        tmp = write_tmp(INVALID_ARCH)
        tmp.rename(tmp.parent / "arch.json")
        path = tmp.parent / "arch.json"
        try:
            r = run("Write", path, json.dumps(INVALID_ARCH))
            self.assertEqual(r.returncode, 1)
            out = json.loads(r.stdout)
            error = out["hookSpecificOutput"]["userFacingError"]
            self.assertIn("arch.json", error)
            self.assertIn("required", error.lower())
        finally:
            path.unlink(missing_ok=True)

    def test_valid_output_json_silent(self):
        tmp = write_tmp(VALID_OUTPUT)
        path = tmp.parent / "Foo.swift.output.json"
        tmp.rename(path)
        try:
            r = run("Write", path, json.dumps(VALID_OUTPUT))
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "")
        finally:
            path.unlink(missing_ok=True)

    def test_invalid_output_json_reports_errors(self):
        tmp = write_tmp(INVALID_OUTPUT)
        path = tmp.parent / "Bar.swift.output.json"
        tmp.rename(path)
        try:
            r = run("Write", path, json.dumps(INVALID_OUTPUT))
            self.assertEqual(r.returncode, 1)
            out = json.loads(r.stdout)
            error = out["hookSpecificOutput"]["userFacingError"]
            self.assertIn("output.json", error)
        finally:
            path.unlink(missing_ok=True)

    def test_edit_tool_also_validated(self):
        tmp = write_tmp(INVALID_ARCH)
        tmp.rename(tmp.parent / "arch.json")
        path = tmp.parent / "arch.json"
        try:
            r = run("Edit", path, "")
            self.assertEqual(r.returncode, 1)
        finally:
            path.unlink(missing_ok=True)


class TestUnknownFiles(unittest.TestCase):
    def test_unknown_json_name_silent(self):
        tmp = write_tmp({"foo": "bar"})
        try:
            r = run("Write", tmp, json.dumps({"foo": "bar"}))
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "")
        finally:
            tmp.unlink(missing_ok=True)

    def test_non_json_file_silent(self):
        with tempfile.NamedTemporaryFile(suffix=".swift", delete=False) as f:
            f.write(b"struct Foo {}")
            path = Path(f.name)
        try:
            r = run("Write", path, "struct Foo {}")
            self.assertEqual(r.returncode, 0)
        finally:
            path.unlink(missing_ok=True)

    def test_nonexistent_file_silent(self):
        r = run("Write", "/tmp/nonexistent-arch.json", "{}")
        self.assertEqual(r.returncode, 0)


class TestToolFilter(unittest.TestCase):
    def test_read_tool_ignored(self):
        tmp = write_tmp(INVALID_ARCH)
        tmp.rename(tmp.parent / "arch.json")
        path = tmp.parent / "arch.json"
        try:
            r = run("Read", path, "")
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "")
        finally:
            path.unlink(missing_ok=True)

    def test_bash_tool_ignored(self):
        r = run("Bash", "/tmp/arch.json", "")
        self.assertEqual(r.returncode, 0)


class TestEdgeCases(unittest.TestCase):
    def test_malformed_event_json_exits_cleanly(self):
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PROJECT_ROOT)}
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json", capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0)

    def test_missing_file_path_exits_cleanly(self):
        event = {"tool_name": "Write", "tool_input": {}}
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PROJECT_ROOT)}
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(event), capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0)

    def test_malformed_json_in_file_reports_parse_error(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", prefix="arch", delete=False
        ) as f:
            f.write("{ not valid json")
            path = Path(f.name)
        # rename to arch.json so schema is found
        arch_path = path.parent / "arch.json"
        path.rename(arch_path)
        try:
            r = run("Write", arch_path, "{ not valid json")
            self.assertEqual(r.returncode, 1)
            self.assertIn("Invalid JSON", r.stdout)
        finally:
            arch_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
