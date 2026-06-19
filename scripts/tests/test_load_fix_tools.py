"""Gateway CLI tests for load_fix_for_violation and load_fix_instructions_for_findings."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATEWAY = PROJECT_ROOT / "mcp-server" / "gateway.py"


def _run_gateway(*args):
    return subprocess.run(
        [sys.executable, str(GATEWAY), *args],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )


def _write_findings(findings):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".output.json", delete=False)
    json.dump({"findings": findings}, f)
    f.close()
    return f.name


class TestLoadFixForViolationGateway(unittest.TestCase):
    def _run(self, metric_id):
        return _run_gateway("load_fix_for_violation", "--metric_ids", metric_id)

    def test_ocp_1_returns_content(self):
        r = self._run("OCP-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OCP-1", r.stdout)
        self.assertGreater(len(r.stdout.strip()), 0)

    def test_unknown_metric_returns_no_fix_message(self):
        r = self._run("OCP-99")
        self.assertEqual(r.returncode, 0)  # fail-open: no exit 1
        self.assertIn("No fix file found", r.stdout)

    def test_completely_unknown_metric_returns_no_fix_message(self):
        r = self._run("BOGUS-99")
        self.assertEqual(r.returncode, 0)
        self.assertIn("No fix file found", r.stdout)

    def test_metric_id_normalised(self):
        r = self._run("ocp-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OCP-1", r.stdout)

    def test_all_core_metrics_have_files(self):
        cases = [
            "SRP-1", "SRP-2", "SRP-3",
            "OCP-1", "OCP-2",
            "LSP-1", "LSP-2", "LSP-3",
            "ISP-1", "ISP-2", "ISP-3",
            "DRY-1", "DRY-2", "DRY-3",
        ]
        for metric_id in cases:
            with self.subTest(metric=metric_id):
                r = self._run(metric_id)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("No fix file found", r.stdout, msg=f"Missing fix for {metric_id}")
                self.assertGreater(len(r.stdout.strip()), 0)


class TestLoadFixInstructionsForFindingsGateway(unittest.TestCase):
    def _run(self, findings_path):
        return _run_gateway("load_fix_instructions_for_findings",
                            "--findings_path", findings_path)

    def test_single_finding_returns_loaded_entry(self):
        path = _write_findings([{"metric_id": "OCP-1"}])
        r = self._run(path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OCP-1", r.stdout)
        self.assertGreater(len(r.stdout.strip()), 50)

    def test_deduplicates_same_metric(self):
        path = _write_findings([{"metric_id": "OCP-1"}, {"metric_id": "OCP-1"}])
        r = self._run(path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("OCP-1 Fix Strategy"), 1)

    def test_mixed_metrics_all_resolved(self):
        path = _write_findings([{"metric_id": "OCP-1"}, {"metric_id": "LSP-3"}])
        r = self._run(path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OCP-1", r.stdout)
        self.assertIn("LSP-3", r.stdout)

    def test_bad_metric_appears_in_missing(self):
        path = _write_findings([{"metric_id": "OCP-99"}])
        r = self._run(path)
        self.assertEqual(r.returncode, 0)  # fail-open
        self.assertIn("OCP-99", r.stdout)

    def test_missing_file_returns_error(self):
        r = self._run("/tmp/does_not_exist_abc123.json")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Could not read", r.stdout)

    def test_accepts_metric_field_alias(self):
        # Review findings use "metric" not "metric_id"
        path = _write_findings([{"metric": "SRP-2"}])
        r = self._run(path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SRP-2", r.stdout)

    def test_old_findings_format_with_principle_still_works(self):
        # Findings that include explicit principle field are still handled
        path = _write_findings([{"principle": "OCP", "metric_id": "OCP-1"}])
        r = self._run(path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OCP-1", r.stdout)


if __name__ == "__main__":
    unittest.main()
