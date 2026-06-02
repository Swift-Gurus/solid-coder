"""
solid-name: TestExpectationLoader
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Verifies that expectation files are correctly parsed from well-formed JSON and that the loader exits with a failure code when files are absent or malformed.
"""

import json
import tempfile
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE)

from expectation_loader import ExpectationLoader


class TestExpectationLoader(unittest.TestCase):
    def _write_expectation(self, directory: Path, stem: str, data: dict) -> Path:
        path = directory / (stem + ".json")
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_empty_findings_list_produces_compliant_expectation(self):
        with tempfile.TemporaryDirectory() as d:
            path = self._write_expectation(Path(d), "fixture-3", {"findings": []})
            expectation = ExpectationLoader().load(path)
            self.assertEqual(expectation.findings, [])

    def test_findings_with_metrics_are_parsed(self):
        with tempfile.TemporaryDirectory() as d:
            data = {
                "findings": [
                    {
                        "unit_name": "UserManager",
                        "metric_id": "SRP-2",
                        "severity": "SEVERE",
                        "metrics": {"cohesion_groups": 2},
                    }
                ]
            }
            path = self._write_expectation(Path(d), "fixture-1", data)
            expectation = ExpectationLoader().load(path)
            self.assertEqual(len(expectation.findings), 1)
            finding = expectation.findings[0]
            self.assertEqual(finding.unit_name, "UserManager")
            self.assertEqual(finding.metric_id, "SRP-2")
            self.assertEqual(finding.severity, "SEVERE")
            self.assertEqual(finding.metrics, {"cohesion_groups": 2})

    def test_finding_without_metrics_field_defaults_to_none(self):
        with tempfile.TemporaryDirectory() as d:
            data = {
                "findings": [
                    {"unit_name": "X", "metric_id": "OCP-1", "severity": "MINOR"}
                ]
            }
            path = self._write_expectation(Path(d), "fixture-2", data)
            expectation = ExpectationLoader().load(path)
            self.assertIsNone(expectation.findings[0].metrics)

    def test_exits_when_expectation_file_does_not_exist(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "missing.json"
            with self.assertRaises(SystemExit) as ctx:
                ExpectationLoader().load(missing)
            self.assertEqual(ctx.exception.code, 1)

    def test_exits_when_expectation_file_contains_invalid_json(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.json"
            path.write_text("not valid json", encoding="utf-8")
            with self.assertRaises(SystemExit) as ctx:
                ExpectationLoader().load(path)
            self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
