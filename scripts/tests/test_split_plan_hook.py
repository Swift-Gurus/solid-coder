"""Tests for hooks/split_plan_on_write.py.

Contract:
  - When Write/Edit fires on implementation-plan.json: splits into chunk files
  - Chunks are written to {parent}/implementation-plan/
  - Items grouped by dependency level: independent items in 01, dependents in 02, etc.
  - Silent (exit 0) for non-matching files, non-Write events, malformed JSON
  - Exits 1 with JSON error if split-plan.py fails
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOOK = PROJECT_ROOT / "hooks" / "split_plan_on_write.py"


def run(tool_name, file_path, env_root=None):
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": tool_name,
        "tool_input": {"file_path": str(file_path)},
        "tool_response": {"content": "Written."},
    }
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(env_root or PROJECT_ROOT)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True, text=True, env=env,
    )


def write_plan(path, items):
    plan = {
        "spec_summary": "test",
        "matched_tags": ["srp"],
        "plan_items": items,
        "reconciliation_decisions": [],
        "summary": {"create": len(items), "modify": 0, "reuse": 0},
    }
    Path(path).write_text(json.dumps(plan), encoding="utf-8")


def make_item(id_, depends_on=None):
    return {
        "id": id_,
        "action": "create",
        "directive": f"implement {id_}",
        "depends_on": depends_on or [],
        "acceptance_criteria": [],
    }


class TestSplitOnWrite(unittest.TestCase):
    def test_splits_independent_items_into_chunk_01(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001"), make_item("plan-002")])
            r = run("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunk_dir = Path(tmp) / "implementation-plan"
            chunks = sorted(chunk_dir.glob("*.json"))
            self.assertEqual(len(chunks), 1, "all independent items → one chunk")
            items = json.loads(chunks[0].read_text())["plan_items"]
            self.assertEqual(len(items), 2)

    def test_splits_dependent_items_into_separate_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [
                make_item("plan-001"),
                make_item("plan-002", depends_on=["plan-001"]),
            ])
            r = run("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunk_dir = Path(tmp) / "implementation-plan"
            chunks = sorted(chunk_dir.glob("*.json"))
            self.assertEqual(len(chunks), 2)
            self.assertEqual(chunks[0].name, "01-plan.json")
            self.assertEqual(chunks[1].name, "02-plan.json")

    def test_chunk_01_contains_level_0_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [
                make_item("plan-001"),
                make_item("plan-002", depends_on=["plan-001"]),
                make_item("plan-003", depends_on=["plan-002"]),
            ])
            r = run("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunk_dir = Path(tmp) / "implementation-plan"
            c1 = json.loads((chunk_dir / "01-plan.json").read_text())
            self.assertEqual([i["id"] for i in c1["plan_items"]], ["plan-001"])

    def test_edit_tool_also_triggers_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001")])
            r = run("Edit", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunk_dir = Path(tmp) / "implementation-plan"
            self.assertTrue(chunk_dir.exists())
            self.assertGreater(len(list(chunk_dir.glob("*.json"))), 0)

    def test_each_chunk_carries_matched_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001")])
            run("Write", plan_path)
            chunk = json.loads((Path(tmp) / "implementation-plan" / "01-plan.json").read_text())
            self.assertIn("matched_tags", chunk)


class TestSilentCases(unittest.TestCase):
    def test_non_plan_json_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "arch.json"
            other.write_text("{}")
            r = run("Write", other)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunk_dir = Path(tmp) / "arch"
            self.assertFalse(chunk_dir.exists())

    def test_read_tool_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001")])
            r = run("Read", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse((Path(tmp) / "implementation-plan").exists())

    def test_nonexistent_file_is_ignored(self):
        r = run("Write", "/tmp/nonexistent-implementation-plan.json")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_malformed_event_json_exits_cleanly(self):
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PROJECT_ROOT)}
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json", capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
