#!/usr/bin/env python3
"""Unit tests for build-spec/scripts/spec-query.py"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT = os.path.join(os.path.dirname(__file__), "build-spec-query.py")


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


class TestTypes(unittest.TestCase):
    def test_returns_four_types(self):
        code, out, _ = run(["types"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("epic", data)
        self.assertIn("feature", data)
        self.assertIn("bug", data)
        self.assertIn("subtask", data)
        self.assertEqual(len(data), 4)


class TestStatuses(unittest.TestCase):
    def test_returns_four_statuses(self):
        code, out, _ = run(["statuses"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("draft", data)
        self.assertIn("ready", data)
        self.assertIn("in-progress", data)
        self.assertIn("done", data)
        self.assertEqual(len(data), 4)


class TestResolvePath(unittest.TestCase):
    def test_root_epic(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["resolve-path", "epic", "SPEC-001", "my-epic"], tmp)
            self.assertEqual(code, 0)
            path = json.loads(out)["path"]
            self.assertTrue(path.endswith("SPEC-001-my-epic/SPEC-001-my-epic.md"))

    def test_feature_under_epic(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp) / "SPEC-001-my-epic", "SPEC-001", "my-epic", "epic", "draft")
            code, out, _ = run(["resolve-path", "feature", "SPEC-002", "my-feature", "--parent", "SPEC-001"], tmp)
            self.assertEqual(code, 0)
            path = json.loads(out)["path"]
            self.assertTrue(path.endswith("features/SPEC-002-my-feature.md"))

    def test_subtask_under_feature(self):
        with TemporaryDirectory() as tmp:
            feat_dir = Path(tmp) / "SPEC-001-epic" / "features"
            make_spec(feat_dir, "SPEC-002", "my-feature", "feature", "draft", "SPEC-001")
            code, out, _ = run(["resolve-path", "subtask", "SPEC-003", "my-subtask", "--parent", "SPEC-002"], tmp)
            self.assertEqual(code, 0)
            path = json.loads(out)["path"]
            self.assertTrue(path.endswith("subtasks/SPEC-003-my-subtask.md"))

    def test_bug_under_feature(self):
        with TemporaryDirectory() as tmp:
            feat_dir = Path(tmp) / "SPEC-001-epic" / "features"
            make_spec(feat_dir, "SPEC-002", "my-feature", "feature", "draft", "SPEC-001")
            code, out, _ = run(["resolve-path", "bug", "SPEC-003", "my-bug", "--parent", "SPEC-002"], tmp)
            self.assertEqual(code, 0)
            path = json.loads(out)["path"]
            self.assertTrue(path.endswith("bugs/SPEC-003-my-bug.md"))

    def test_missing_parent_for_feature(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["resolve-path", "feature", "SPEC-002", "my-feature"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("missing_parent", out)

    def test_invalid_type(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["resolve-path", "unknown", "SPEC-001", "slug"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("invalid_type", out)


class TestUpdateStatus(unittest.TestCase):
    def test_updates_status_field(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "my-epic", "epic", "draft")
            code, out, _ = run(["update-status", "SPEC-001", "ready"], tmp)
            self.assertEqual(code, 0)
            content = (Path(tmp) / "SPEC-001-my-epic.md").read_text()
            self.assertIn("status: ready", content)

    def test_returns_modified_list(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "my-epic", "epic", "draft")
            code, out, _ = run(["update-status", "SPEC-001", "ready"], tmp)
            data = json.loads(out)
            self.assertIn("modified", data)
            self.assertEqual(len(data["modified"]), 1)

    def test_invalid_status(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "my-epic", "epic", "draft")
            code, out, _ = run(["update-status", "SPEC-001", "invalid"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("invalid_status", out)

    def test_not_found(self):
        with TemporaryDirectory() as tmp:
            code, out, _ = run(["update-status", "SPEC-999", "ready"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("not_found", out)

    def test_blocked_by_draft_children(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "my-epic", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "my-feat", "feature", "draft", "SPEC-001")
            code, out, _ = run(["update-status", "SPEC-001", "ready"], tmp)
            self.assertEqual(code, 1)
            self.assertIn("blocked_by_draft_children", out)

    def test_propagates_ready_to_parent(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "root-epic", "epic", "draft")
            make_spec(Path(tmp), "SPEC-002", "feat-a", "feature", "ready", "SPEC-001")
            make_spec(Path(tmp), "SPEC-003", "feat-b", "feature", "draft", "SPEC-001")
            run(["update-status", "SPEC-003", "ready"], tmp)
            content = (Path(tmp) / "SPEC-001-root-epic.md").read_text()
            self.assertIn("status: ready", content)

    def test_propagates_done_to_parent(self):
        with TemporaryDirectory() as tmp:
            make_spec(Path(tmp), "SPEC-001", "root-epic", "epic", "ready")
            make_spec(Path(tmp), "SPEC-002", "feat-a", "feature", "done", "SPEC-001")
            make_spec(Path(tmp), "SPEC-003", "feat-b", "feature", "ready", "SPEC-001")
            run(["update-status", "SPEC-003", "done"], tmp)
            content = (Path(tmp) / "SPEC-001-root-epic.md").read_text()
            self.assertIn("status: done", content)


if __name__ == "__main__":
    unittest.main()
