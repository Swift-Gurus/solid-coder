"""Tests for mcp-server/pipeline/server.py"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "mcp-server" / "pipeline"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "pipeline_server", ROOT / "mcp-server" / "pipeline" / "server.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestHandshake(unittest.TestCase):
    def test_all_tools_registered(self):
        for name in ("check_severity", "validate_findings", "load_synthesis_context",
                     "generate_report", "validate_architecture", "split_implementation_plan",
                     "search_codebase", "prepare_review_input"):
            self.assertTrue(hasattr(mod, name), f"missing tool: {name}")


class TestCollectReviewResults(unittest.TestCase):
    def _make_review(self, tmp, principle, severity):
        rules = Path(tmp) / "rules" / principle
        rules.mkdir(parents=True)
        import json
        (rules / "review-output.json").write_text(json.dumps({
            "files": [{"units": [{"findings": [{"severity": severity}]}]}]
        }))

    def test_no_rules_dir_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.collect_review_results(output_root=tmp)
            self.assertIn("error", result)

    def test_all_compliant(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_review(tmp, "SRP", "COMPLIANT")
            result = mod.collect_review_results(output_root=tmp)
            self.assertEqual(result["verdict"], "ALL_COMPLIANT")
            self.assertEqual(len(result["summary"]), 1)

    def test_minor_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_review(tmp, "OCP", "MINOR")
            result = mod.collect_review_results(output_root=tmp)
            self.assertEqual(result["verdict"], "MINOR_ONLY")
            self.assertEqual(result["total_minor"], 1)

    def test_has_severe(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_review(tmp, "SRP", "SEVERE")
            self._make_review(tmp, "OCP", "MINOR")
            result = mod.collect_review_results(output_root=tmp)
            self.assertEqual(result["verdict"], "HAS_SEVERE")
            self.assertEqual(result["total_severe"], 1)
            self.assertEqual(result["total_minor"], 1)


class TestCheckSeverity(unittest.TestCase):
    def test_missing_rules_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                mod.check_severity(output_root=tmp)
            except FileNotFoundError:
                pass  # expected — no rules/ subdir
            except Exception as e:
                self.fail(f"Unexpected exception: {e}")

    def test_all_compliant_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "rules").mkdir()
            result = mod.check_severity(output_root=tmp)
            self.assertIsInstance(result, (dict, str))


class TestValidateFindings(unittest.TestCase):
    def test_missing_dir_returns_error(self):
        result = mod.validate_findings(output_root="/nonexistent/path")
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("success", True))


class TestGenerateReport(unittest.TestCase):
    def test_empty_dir_runs_without_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.generate_report(data_dir=tmp)
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)


class TestValidateArchitecture(unittest.TestCase):
    def test_missing_file_returns_error(self):
        result = mod.validate_architecture(arch_path="/nonexistent/arch.json")
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("valid", True))


class TestSplitImplementationPlan(unittest.TestCase):
    def test_missing_plan_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = mod.split_implementation_plan(
                plan_path="/nonexistent/plan.json", output_dir=tmp
            )
            self.assertIsInstance(result, dict)
            self.assertFalse(result.get("success", True))


class TestSearchCodebase(unittest.TestCase):
    def test_no_terms_returns_error(self):
        result = mod.search_codebase(sources_dir=str(ROOT))
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    def test_missing_dir_returns_error(self):
        result = mod.search_codebase(sources_dir="/nonexistent", tags=["foo"])
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    def test_tag_search_returns_text(self):
        result = mod.search_codebase(sources_dir=str(ROOT), tags=["server", "pipeline", "loads"], min_matches=1)
        self.assertIsInstance(result, str)

    def test_plan_path_extracts_terms(self):
        import tempfile, json as _json
        arch = {"components": [{"name": "MCPServer", "category": "service",
                                "interfaces": ["Serving"], "stack": [], "dependencies": []}]}
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            _json.dump(arch, f); plan_path = f.name
        result = mod.search_codebase(sources_dir=str(ROOT), plan_path=plan_path, min_matches=1)
        self.assertIsInstance(result, str)

    def test_no_matches_returns_message(self):
        result = mod.search_codebase(sources_dir=str(ROOT), tags=["zzz_nonexistent_term"], min_matches=1)
        self.assertIn("No files matched", result)

    def test_output_has_instructions(self):
        result = mod.search_codebase(sources_dir=str(ROOT), tags=["server", "loads", "strips"], min_matches=1)
        if "No files" not in result and "Error" not in result and "Read" not in result:
            self.assertIn("Review", result)


if __name__ == "__main__":
    unittest.main()
