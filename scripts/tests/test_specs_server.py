"""Tests for mcp-server/specs/server.py"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "mcp-server"))
sys.path.insert(0, str(ROOT / "mcp-server" / "specs"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "specs_server", ROOT / "mcp-server" / "specs" / "server.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestParseSpec(unittest.TestCase):
    def test_parses_valid_spec(self):
        # Find any real spec file in the project
        specs_root = ROOT / ".claude" / "specs"
        spec_files = list(specs_root.rglob("Spec.md")) if specs_root.exists() else []
        if not spec_files:
            self.skipTest("No spec files found")
        result = mod.parse_spec(file_path=str(spec_files[0]))
        self.assertIsInstance(result, dict)
        self.assertIn("number", result)

    def test_missing_file_returns_error(self):
        result = mod.parse_spec(file_path="/nonexistent/Spec.md")
        self.assertIsInstance(result, str)
        self.assertIn("not found", result.lower())


class TestQuerySpecs(unittest.TestCase):
    def test_scan_returns_list(self):
        result = mod.query_specs(action="scan")
        self.assertIsInstance(result, list)

    def test_next_number_returns_dict(self):
        result = mod.query_specs(action="next-number")
        self.assertIsInstance(result, dict)
        self.assertIn("next", result)

    def test_types_returns_list(self):
        result = mod.query_specs(action="types")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_statuses_returns_list(self):
        result = mod.query_specs(action="statuses")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_unknown_spec_ancestors_returns_error(self):
        result = mod.query_specs(action="ancestors", args=["SPEC-999"])
        self.assertIsInstance(result, str)

    def test_children_of_unknown_returns_error(self):
        result = mod.query_specs(action="children", args=["SPEC-999"])
        self.assertIsInstance(result, str)


class TestLoadSpecContext(unittest.TestCase):
    def test_unknown_spec_returns_message(self):
        result = mod.load_spec_context(spec_number="SPEC-999")
        self.assertIsInstance(result, str)

    def test_known_spec_returns_text(self):
        specs = mod.query_specs(action="scan")
        if not specs or not isinstance(specs, list):
            self.skipTest("No specs found")
        first = specs[0].get("number")
        if not first:
            self.skipTest("No spec number found")
        result = mod.load_spec_context(spec_number=first)
        self.assertIsInstance(result, str)
        self.assertIn(first, result)

    def test_file_path_resolves_spec_number(self):
        specs = mod.query_specs(action="scan")
        if not specs or not isinstance(specs, list):
            self.skipTest("No specs found")
        path = specs[0].get("path")
        if not path:
            self.skipTest("No spec path found")
        result = mod.load_spec_context(file_path=path)
        self.assertIsInstance(result, str)
        self.assertIn(specs[0]["number"], result)

    def test_no_args_returns_error(self):
        result = mod.load_spec_context()
        self.assertIn("Error", result)

    def test_missing_file_path_returns_error(self):
        result = mod.load_spec_context(file_path="/nonexistent/Spec.md")
        self.assertIn("Error", result)


class TestHandshake(unittest.TestCase):
    def test_server_module_loads(self):
        self.assertTrue(hasattr(mod, "parse_spec"))
        self.assertTrue(hasattr(mod, "query_specs"))
        self.assertTrue(hasattr(mod, "load_spec_context"))
        self.assertTrue(hasattr(mod, "update_spec_status"))


if __name__ == "__main__":
    unittest.main()
