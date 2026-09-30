"""Tests for mcp-server/pipeline/server.py"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEARCH_FIXTURES = ROOT / "skills" / "validate-plan" / "scripts" / "test_fixtures"
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "mcp-server" / "pipeline"))

from pipeline.application_bootstrapper_factory import ApplicationBootstrapperFactory
from pipeline.flow_result_renderer_creator import FlowResultRendererCreator
from pipeline.flow_run_creator import FlowRunCreator

tools = ApplicationBootstrapperFactory(
    plugin_root=ROOT,
    skills_root=ROOT / "skills",
    flow_run_creator=FlowRunCreator(ROOT),
    flow_renderer_creator=FlowResultRendererCreator(),
).make_tool_callables().build()


class TestHandshake(unittest.TestCase):
    def test_all_tools_registered(self):
        for name in ("check_severity", "validate_findings", "load_synthesis_context",
                     "generate_report", "validate_architecture", "split_implementation_plan",
                     "search_codebase", "prepare_review_input"):
            self.assertIn(name, tools, f"missing tool: {name}")


class TestCollectReviewResults(unittest.TestCase):
    def _make_review(self, tmp, principle, severity):
        rules = Path(tmp) / "rules" / principle
        rules.mkdir(parents=True)
        import json
        (rules / "review-output.json").write_text(json.dumps({
            "files": [{"units": [{"violations": [{"severity": severity}]}]}]
        }))

    def test_no_rules_dir_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = tools["collect_review_results"](output_root=tmp)
            self.assertIn("error", result)

    def test_all_compliant(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_review(tmp, "SRP", "COMPLIANT")
            result = tools["collect_review_results"](output_root=tmp)
            self.assertEqual(result["verdict"], "ALL_COMPLIANT")
            self.assertEqual(len(result["summary"]), 1)

    def test_minor_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_review(tmp, "OCP", "MINOR")
            result = tools["collect_review_results"](output_root=tmp)
            self.assertEqual(result["verdict"], "MINOR_ONLY")
            self.assertEqual(result["total_minor"], 1)

    def test_has_severe(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_review(tmp, "SRP", "SEVERE")
            self._make_review(tmp, "OCP", "MINOR")
            result = tools["collect_review_results"](output_root=tmp)
            self.assertEqual(result["verdict"], "HAS_SEVERE")
            self.assertEqual(result["total_severe"], 1)
            self.assertEqual(result["total_minor"], 1)


class TestCheckSeverity(unittest.TestCase):
    def test_missing_rules_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                tools["check_severity"](output_root=tmp)
            except FileNotFoundError:
                pass  # expected — no rules/ subdir
            except Exception as e:
                self.fail(f"Unexpected exception: {e}")

    def test_all_compliant_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "rules").mkdir()
            result = tools["check_severity"](output_root=tmp)
            self.assertIsInstance(result, (dict, str))


class TestValidateFindings(unittest.TestCase):
    def test_missing_dir_returns_error(self):
        result = tools["validate_findings"](output_root="/nonexistent/path")
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("success", True))


class TestGenerateReport(unittest.TestCase):
    def test_empty_dir_runs_without_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = tools["generate_report"](data_dir=tmp)
            self.assertIsInstance(result, dict)
            self.assertIn("success", result)


class TestValidateArchitecture(unittest.TestCase):
    def test_missing_file_returns_error(self):
        result = tools["validate_architecture"](arch_path="/nonexistent/arch.json")
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("valid", True))


class TestSplitImplementationPlan(unittest.TestCase):
    def test_missing_plan_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = tools["split_implementation_plan"](
                plan_path="/nonexistent/plan.json", output_dir=tmp
            )
            self.assertIsInstance(result, dict)
            self.assertFalse(result.get("success", True))


class TestSearchCodebase(unittest.TestCase):
    def test_no_terms_returns_error(self):
        result = tools["search_codebase"](sources_dir=str(SEARCH_FIXTURES))
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    def test_missing_dir_returns_error(self):
        result = tools["search_codebase"](sources_dir="/nonexistent", tags=["foo"])
        self.assertIsInstance(result, str)
        self.assertIn("Error", result)

    def test_tag_search_returns_text(self):
        result = tools["search_codebase"](
            sources_dir=str(SEARCH_FIXTURES), tags=["network", "product", "fetches"], min_matches=1,
        )
        self.assertIsInstance(result, str)
        self.assertIn("unit: ProductFetchService.swift\n", result)
        self.assertIn(f"path: {SEARCH_FIXTURES / 'ProductFetchService.swift'}", result)

    def test_plan_path_extracts_terms(self):
        import json
        arch = {"components": [{"name": "ProductFetchService", "category": "network",
                                "interfaces": ["ProductReading"], "stack": [], "dependencies": []}]}
        with tempfile.TemporaryDirectory() as temporary:
            plan_path = Path(temporary) / "architecture.json"
            plan_path.write_text(json.dumps(arch), encoding="utf-8")
            result = tools["search_codebase"](
                sources_dir=str(SEARCH_FIXTURES), plan_path=str(plan_path), min_matches=1,
            )
        self.assertIsInstance(result, str)
        self.assertIn("unit: ProductFetchService.swift\n", result)

    def test_no_matches_returns_message(self):
        result = tools["search_codebase"](
            sources_dir=str(SEARCH_FIXTURES), tags=["zzz_nonexistent_term"], min_matches=1,
        )
        self.assertEqual(result, f"No files matched in {SEARCH_FIXTURES} (7 files scanned).")

    def test_output_has_candidate_summary(self):
        result = tools["search_codebase"](
            sources_dir=str(SEARCH_FIXTURES), tags=["network"], min_matches=1,
        )
        self.assertEqual(result, "\n".join([
            "Here is what we found:",
            "",
            "candidate_id: candidate-1",
            "unit: ProductFetchService.swift",
            "description: Fetches product data from REST API with pagination",
            f"path: {SEARCH_FIXTURES / 'ProductFetchService.swift'}",
        ]))


if __name__ == "__main__":
    unittest.main()
