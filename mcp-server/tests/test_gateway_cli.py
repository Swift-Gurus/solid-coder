"""
solid-description: Regression suite verifying that all MCP gateway tools are registered and reachable via the command-line interface.
solid-category: unit-test
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

GATEWAY = Path(__file__).resolve().parents[1] / "gateway.py"


def _run(*args):
    return subprocess.run(
        [sys.executable, str(GATEWAY)] + list(args),
        capture_output=True,
        text=True,
    )


class TestGatewayCliLoadDetectionRules(unittest.TestCase):
    """Regression tests: load_detection_rules must be callable via gateway CLI."""

    def test_no_args_exits_zero(self):
        result = _run("load_detection_rules")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_args_returns_principles_key(self):
        result = _run("load_detection_rules")
        data = json.loads(result.stdout)
        self.assertIn("principles", data)
        self.assertGreater(len(data["principles"]), 0)

    def test_matched_tags_filters_to_fewer_principles(self):
        all_result = _run("load_detection_rules")
        filtered_result = _run("load_detection_rules", "--matched_tags", "unit-test")
        self.assertEqual(all_result.returncode, 0, all_result.stderr)
        self.assertEqual(filtered_result.returncode, 0, filtered_result.stderr)
        all_count = len(json.loads(all_result.stdout)["principles"])
        filtered_count = len(json.loads(filtered_result.stdout)["principles"])
        # "unit-test" activates always-on principles + Unit Testing; other
        # conditional principles (swiftui, structured-concurrency) are excluded.
        self.assertGreater(filtered_count, 0, "tag filter returned no principles")
        self.assertLess(filtered_count, all_count)

    def test_principle_arg_returns_single_principle(self):
        result = _run("load_detection_rules", "--principle", "SRP")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(len(data["principles"]), 1)

    def test_unknown_principle_exits_zero_with_error_key(self):
        result = _run("load_detection_rules", "--principle", "NONEXISTENT_XYZ")
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("error", data)


class TestGatewayCliRegistration(unittest.TestCase):
    """Smoke tests: verify all expected tools are registered in the CLI."""

    REQUIRED_TOOLS = [
        "get_candidate_tags",
        "discover_principles",
        "load_rules",
        "load_detection_rules",
        "check_severity",
        "load_synthesis_context",
        "validate_findings",
        "generate_report",
        "search_codebase",
        "load_fix_for_violation",
        "load_fix_instructions_for_findings",
    ]

    def test_unknown_tool_exits_nonzero(self):
        result = _run("totally_unknown_tool_xyz")
        self.assertNotEqual(result.returncode, 0)

    def test_all_required_tools_listed_in_help(self):
        result = _run("help")
        self.assertEqual(result.returncode, 0)
        for tool in self.REQUIRED_TOOLS:
            self.assertIn(tool, result.stdout + result.stderr, f"Missing from help: {tool}")


if __name__ == "__main__":
    unittest.main()
