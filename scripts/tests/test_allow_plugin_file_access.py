"""Tests for hooks/allow_plugin_file_access.py.

Contract:
  - Returns behavior=allow for files inside CLAUDE_PLUGIN_ROOT
  - Returns behavior=allow for files inside {CLAUDE_PROJECT_DIR}/.solid_coder/
  - Returns behavior=allow for files inside {CLAUDE_PROJECT_DIR}/.claude/specs/
  - Returns behavior=ask for everything else
  - Exits 0 in all cases (never blocks)
  - Handles missing file_path gracefully
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOOK = PROJECT_ROOT / "hooks" / "allow_plugin_file_access.py"
FAKE_PROJECT = "/Users/alex/MyApp"


def run(tool_name, file_path=None, project_dir=FAKE_PROJECT):
    tool_input = {}
    if file_path is not None:
        tool_input["file_path"] = str(file_path)
    event = {"hook_event_name": "PermissionRequest", "tool_name": tool_name, "tool_input": tool_input}
    env = {
        **os.environ,
        "CLAUDE_PLUGIN_ROOT": str(PROJECT_ROOT),
        "CLAUDE_PROJECT_DIR": str(project_dir),
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True, text=True, env=env,
    )


def decision(r):
    return json.loads(r.stdout)["hookSpecificOutput"]["decision"]["behavior"]


class TestPluginFiles(unittest.TestCase):
    def test_allows_references_file(self):
        r = run("Read", PROJECT_ROOT / "references" / "principles" / "SRP" / "rule.md")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_allows_hooks_dir_file(self):
        r = run("Write", PROJECT_ROOT / "hooks" / "hooks.json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_allows_mcp_server_file(self):
        r = run("Edit", PROJECT_ROOT / "mcp-server" / "server.py")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")


class TestOutputDirectory(unittest.TestCase):
    def test_allows_solid_coder_output_file(self):
        r = run("Write", f"{FAKE_PROJECT}/.solid_coder/review-123/by-file/Foo.swift.output.json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_allows_nested_solid_coder_path(self):
        r = run("Read", f"{FAKE_PROJECT}/.solid_coder/review-123/synthesized/Bar.swift.plan.json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_blocks_solid_coder_in_different_project(self):
        r = run("Write", "/Users/other/OtherApp/.solid_coder/review-123/report.html")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "ask")


class TestSpecDirectory(unittest.TestCase):
    def test_allows_spec_file(self):
        r = run("Read", f"{FAKE_PROJECT}/.claude/specs/SPEC-001-login/Spec.md")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_allows_spec_resources(self):
        r = run("Read", f"{FAKE_PROJECT}/.claude/specs/SPEC-001-login/resources/design.png")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_blocks_other_claude_dir_files(self):
        r = run("Read", f"{FAKE_PROJECT}/.claude/CLAUDE.md")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "ask")

    def test_blocks_specs_in_different_project(self):
        r = run("Read", "/Users/other/OtherApp/.claude/specs/SPEC-001/Spec.md")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "ask")

    def test_allows_root_level_specs_folder(self):
        r = run("Read", f"{FAKE_PROJECT}/specs/SPEC-001-login/Spec.md")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_allows_root_level_specs_resources(self):
        r = run("Read", f"{FAKE_PROJECT}/specs/SPEC-002/resources/wireframe.png")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")

    def test_blocks_root_level_specs_in_different_project(self):
        r = run("Read", "/Users/other/OtherApp/specs/SPEC-001/Spec.md")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "ask")


class TestExternalFiles(unittest.TestCase):
    def test_asks_for_project_source_file(self):
        r = run("Read", f"{FAKE_PROJECT}/Sources/App/ContentView.swift")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "ask")

    def test_asks_for_tmp_file(self):
        r = run("Write", "/tmp/something.json")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "ask")


class TestEdgeCases(unittest.TestCase):
    def test_no_file_path_exits_cleanly(self):
        r = run("Read", file_path=None)
        self.assertEqual(r.returncode, 0)

    def test_malformed_json_exits_cleanly(self):
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PROJECT_ROOT), "CLAUDE_PROJECT_DIR": FAKE_PROJECT}
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json", capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0)

    def test_no_project_dir_env_still_allows_plugin_files(self):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
        env["CLAUDE_PLUGIN_ROOT"] = str(PROJECT_ROOT)
        event = {"hook_event_name": "PermissionRequest", "tool_name": "Read",
                 "tool_input": {"file_path": str(PROJECT_ROOT / "mcp-server" / "server.py")}}
        r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event),
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(decision(r), "allow")


if __name__ == "__main__":
    unittest.main()
