"""solid-description: Tests that proposed fixes are validated for complete violation coverage and appropriate status is returned.
solid-category: unit-test
"""

import json
import unittest
from pathlib import Path
from helpers import SubmitFindingsTestBase


def _write_review_output(tmp_dir: str, label: str, violations: list) -> None:
    p = Path(tmp_dir) / label
    p.mkdir(parents=True, exist_ok=True)
    (p / "review-output.json").write_text(json.dumps({
        "timestamp": "2026-01-01T00:00:00Z",
        "files": [{"file_path": "/tmp/Foo.swift", "units": [{
            "unit_name": "Foo",
            "unit_kind": "class",
            "metrics": {},
            "violations": violations,
        }]}],
    }))


def _severe(rule_id: str) -> dict:
    return {"rule_id": rule_id, "severity": "SEVERE"}


def _fix(rule_id: str, text: str = "Fix it.") -> dict:
    return {"rule_id": rule_id, "file_path": "/tmp/Foo.swift", "unit_name": "Foo", "suggested_fix": text}


class TestSubmitFix(SubmitFindingsTestBase):

    def test_submit_fix_stores_fix_files(self):
        _write_review_output(self.tmp.name, "SRP", [_severe("SRP-2")])
        self.handler.submit_fix(self.tmp.name, [_fix("SRP-2", "Extract Foo.")])
        self.assertEqual(len(list((Path(self.tmp.name) / "fixes").glob("*.json"))), 1)

    def test_submit_fix_returns_complete_for_single_violation(self):
        _write_review_output(self.tmp.name, "SRP", [_severe("SRP-2")])
        result = self.handler.submit_fix(self.tmp.name, [_fix("SRP-2")])
        self.assertTrue(result.get("complete"))

    def test_submit_fix_returns_complete_when_all_violations_covered(self):
        _write_review_output(self.tmp.name, "SRP", [_severe("SRP-1"), _severe("SRP-2")])
        result = self.handler.submit_fix(self.tmp.name, [_fix("SRP-1"), _fix("SRP-2")])
        self.assertTrue(result.get("complete"))

    def test_submit_fix_returns_error_when_violation_missing(self):
        _write_review_output(self.tmp.name, "SRP", [_severe("SRP-1"), _severe("SRP-2")])
        result = self.handler.submit_fix(self.tmp.name, [_fix("SRP-1")])
        self.assertIn("error", result)
        self.assertIn("SRP-2", result["error"])

    def test_submit_fix_complete_includes_suggested_fix_text(self):
        _write_review_output(self.tmp.name, "SRP", [_severe("SRP-2")])
        result = self.handler.submit_fix(self.tmp.name, [_fix("SRP-2", "Extract DbManager.")])
        vwf = result.get("violations_with_fixes", [])
        self.assertEqual(len(vwf), 1)
        self.assertEqual(vwf[0]["suggested_fix"], "Extract DbManager.")

    def test_submit_fix_returns_complete_when_no_violations_exist(self):
        result = self.handler.submit_fix(self.tmp.name, [])
        self.assertTrue(result.get("complete"))
        self.assertEqual(result.get("violations_with_fixes"), [])

    def test_submit_fix_returns_error_on_non_list_input(self):
        result = self.handler.submit_fix(self.tmp.name, "not-a-list")
        self.assertIn("error", result)

    def test_submit_fix_returns_error_on_missing_required_field(self):
        _write_review_output(self.tmp.name, "SRP", [_severe("SRP-2")])
        result = self.handler.submit_fix(self.tmp.name, [{"rule_id": "SRP-2", "file_path": "/tmp/Foo.swift"}])
        self.assertIn("error", result)

    def test_submit_fix_empty_list_returns_error_when_violations_exist(self):
        _write_review_output(self.tmp.name, "SRP", [_severe("SRP-2")])
        result = self.handler.submit_fix(self.tmp.name, [])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
