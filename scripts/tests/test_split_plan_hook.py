"""Tests for hooks/split_plan_on_write.py.

Contract:
  - When Write/Edit fires on implementation-plan.json: splits into chunk files
  - Chunks are written to {parent}/implementation-plan/
  - Without sibling arch.json: items split by dependency level, files named
    xx-implementations.json
  - With sibling arch.json: items classified by component category;
    model/enum/typealias → foundations, unit tests → tests, UI tests → ui-tests
  - Silent (exit 0) for non-matching files, non-Write/Edit events, malformed JSON
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


def run_hook(tool_name, file_path, env_root=None):
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
        "acceptance_criteria": [],
        "plan_items": items,
        "reconciliation_decisions": [],
        "summary": {"create": len(items), "modify": 0, "reuse": 0},
    }
    Path(path).write_text(json.dumps(plan), encoding="utf-8")


def write_arch(path, *components):
    """components: (name, category) pairs."""
    arch = {
        "spec_summary": "test",
        "components": [
            {"name": n, "category": c, "stack": [], "responsibility": "",
             "interfaces": [], "dependencies": [], "produces": [], "fields": []}
            for n, c in components
        ],
        "wiring": [],
        "composition_root": "",
    }
    Path(path).write_text(json.dumps(arch), encoding="utf-8")


def make_item(id_, component="SomeService", depends_on=None, test_cases=None):
    item = {
        "id": id_, "action": "create", "component": component,
        "directive": f"implement {id_}", "depends_on": depends_on or [],
        "notes": "", "acceptance_criteria": [],
    }
    if test_cases is not None:
        item["test_cases"] = test_cases
    return item


class TestSplitOnWrite(unittest.TestCase):
    def test_independent_items_in_one_implementations_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001"), make_item("plan-002")])
            r = run_hook("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunks = sorted((Path(tmp) / "implementation-plan").glob("*.json"))
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0].name, "01-implementations.json")
            self.assertEqual(len(json.loads(chunks[0].read_text())["plan_items"]), 2)

    def test_dependent_items_split_into_separate_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [
                make_item("plan-001"),
                make_item("plan-002", depends_on=["plan-001"]),
            ])
            r = run_hook("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunks = sorted((Path(tmp) / "implementation-plan").glob("*.json"))
            self.assertEqual(len(chunks), 2)
            self.assertEqual(chunks[0].name, "01-implementations.json")
            self.assertEqual(chunks[1].name, "02-implementations.json")

    def test_edit_tool_also_triggers_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001")])
            r = run_hook("Edit", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunk_dir = Path(tmp) / "implementation-plan"
            self.assertTrue(chunk_dir.exists())
            self.assertGreater(len(list(chunk_dir.glob("*.json"))), 0)

    def test_each_chunk_carries_matched_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001")])
            run_hook("Write", plan_path)
            chunk = json.loads(
                (Path(tmp) / "implementation-plan" / "01-implementations.json").read_text()
            )
            self.assertIn("matched_tags", chunk)

    def test_with_arch_model_goes_to_foundations(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001", component="ProductModel")])
            write_arch(Path(tmp) / "arch.json", ("ProductModel", "model"))
            r = run_hook("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunks = sorted((Path(tmp) / "implementation-plan").glob("*.json"))
            self.assertEqual(len(chunks), 1)
            self.assertEqual(chunks[0].name, "01-foundations.json")

    def test_with_arch_unit_test_goes_to_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            tc = {"type": "unit", "description": "t", "given": "g", "when": "w", "expect": "e"}
            write_plan(plan_path, [make_item("plan-001", component="Tests", test_cases=[tc])])
            write_arch(Path(tmp) / "arch.json", ("Tests", "test"))
            r = run_hook("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunks = sorted((Path(tmp) / "implementation-plan").glob("*.json"))
            self.assertEqual(chunks[0].name, "01-tests.json")

    def test_with_arch_ui_test_goes_to_ui_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            tc = {"type": "ui", "description": "t", "given": "g", "when": "w", "expect": "e"}
            write_plan(plan_path, [make_item("plan-001", component="UITests", test_cases=[tc])])
            write_arch(Path(tmp) / "arch.json", ("UITests", "test"))
            r = run_hook("Write", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            chunks = sorted((Path(tmp) / "implementation-plan").glob("*.json"))
            self.assertEqual(chunks[0].name, "01-ui-tests.json")


class TestSilentCases(unittest.TestCase):
    def test_non_plan_json_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "arch.json"
            other.write_text("{}")
            r = run_hook("Write", other)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse((Path(tmp) / "arch").exists())

    def test_read_tool_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "implementation-plan.json"
            write_plan(plan_path, [make_item("plan-001")])
            r = run_hook("Read", plan_path)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse((Path(tmp) / "implementation-plan").exists())

    def test_nonexistent_file_is_ignored(self):
        r = run_hook("Write", "/tmp/nonexistent-implementation-plan.json")
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
