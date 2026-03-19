#!/usr/bin/env python3
"""Unit tests for find-spec/scripts/spec-query.py"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT = os.path.join(os.path.dirname(__file__), "find-spec-query.py")


def run(args: list, specs_root: str = None) -> tuple:
    cmd = [sys.executable, SCRIPT] + args
    if specs_root:
        cmd += ["--specs-root", specs_root]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def make_spec(folder: Path, number: str, feature: str, spec_type: str, status: str, parent: str = "") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{number}-{feature}.md"
    parent_line = f"parent: {parent}" if parent else ""
    path.write_text(f"---\nnumber: {number}\nfeature: {feature}\ntype: {spec_type}\nstatus: {status}\n{parent_line}\n---\n\n# {feature}\n")
    return path


class TestScanBasic(unittest.TestCase):
    def test_returns_all_specs(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "epic-a", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "feat-a", "feature", "ready", "SPEC-001")
            code, out, _ = run(["scan"], tmp)
            self.assertEqual(code, 0)
            data = json.loads(out)
            self.assertEqual(len(data), 2)

    def test_filter_type(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "epic-a", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "feat-a", "feature", "draft", "SPEC-001")
            code, out, _ = run(["scan", "--type", "epic"], tmp)
            data = json.loads(out)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["number"], "SPEC-001")

    def test_filter_status_single(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "epic-a", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "epic-b", "epic", "ready")
            code, out, _ = run(["scan", "--status", "draft"], tmp)
            data = json.loads(out)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["status"], "draft")

    def test_filter_status_multiple(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "epic-a", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "epic-b", "epic", "ready")
            make_spec(Path(tmp), "SPEC-003", "epic-c", "epic", "done")
            code, out, _ = run(["scan", "--status", "draft,ready"], tmp)
            data = json.loads(out)
            self.assertEqual(len(data), 2)

    def test_no_parent_filter(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "root-epic", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "child-feat", "feature", "draft", "SPEC-001")
            code, out, _ = run(["scan", "--no-parent"], tmp)
            data = json.loads(out)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["number"], "SPEC-001")

    def test_parent_filter(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "root-epic", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "feat-a", "feature", "draft", "SPEC-001")
            make_spec(Path(tmp), "SPEC-003", "feat-b", "feature", "ready", "SPEC-001")
            code, out, _ = run(["scan", "--parent", "SPEC-001"], tmp)
            data = json.loads(out)
            self.assertEqual(len(data), 2)

    def test_empty_specs_root(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["scan"], tmp)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out), [])


class TestChildren(unittest.TestCase):
    def test_returns_direct_children(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "epic-a", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "feat-a", "feature", "draft", "SPEC-001")
            make_spec(Path(tmp), "SPEC-003", "feat-b", "feature", "draft", "SPEC-001")
            code, out, _ = run(["children", "SPEC-001"], tmp)
            data = json.loads(out)
            self.assertEqual(len(data), 2)

    def test_not_found(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["children", "SPEC-999"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("not_found", out)


class TestAncestors(unittest.TestCase):
    def test_chain_root_to_leaf(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "root-epic", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "child-feat", "feature", "draft", "SPEC-001")
            code, out, _ = run(["ancestors", "SPEC-002"], tmp)
            data = json.loads(out)
            self.assertEqual(data[0]["number"], "SPEC-001")
            self.assertEqual(data[1]["number"], "SPEC-002")

    def test_single_spec(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "root-epic", "epic", "draft")
            code, out, _ = run(["ancestors", "SPEC-001"], tmp)
            data = json.loads(out)
            self.assertEqual(len(data), 1)

    def test_not_found(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["ancestors", "SPEC-999"], tmp)
            self.assertEqual(code, 1)


class TestNextNumber(unittest.TestCase):
    def test_starts_at_001_when_empty(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["next-number"], tmp)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out)["next"], "SPEC-001")

    def test_increments_from_highest(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "a", "epic", "draft")
            make_spec(Path(tmp), "SPEC-005", "b", "epic", "draft")
            code, out, _ = run(["next-number"], tmp)
            self.assertEqual(json.loads(out)["next"], "SPEC-006")

    def test_zero_padded(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-009", "a", "epic", "draft")
            code, out, _ = run(["next-number"], tmp)
            self.assertEqual(json.loads(out)["next"], "SPEC-010")


if __name__ == "__main__":
    unittest.main()
