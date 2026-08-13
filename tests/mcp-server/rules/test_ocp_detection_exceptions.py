"""Verifies OCP exceptions survive health-prompt construction."""

import sys
import unittest
from pathlib import Path

_TEST_MCP_DIR = Path(__file__).resolve().parents[1]
_MCP_DIR = Path(__file__).resolve().parents[3] / "mcp-server"
for _path in (_TEST_MCP_DIR, _MCP_DIR, _MCP_DIR / "utils"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from helpers import make_handler
from health.health_prompt_builder import HealthPromptBuilder


"""
solid-name: TestOCPDetectionExceptions
solid-category: unit-test
solid-description: Verifies dependency-free and pure-data OCP exceptions survive rule loading and health-prompt assembly.
"""
class TestOCPDetectionExceptions(unittest.TestCase):

    def test_health_prompt_contains_dependency_free_and_pure_data_exceptions(self):
        principle = make_handler().load_detection_rules(
            principle="ocp"
        )["principles"][0]

        prompt = HealthPromptBuilder().build(
            principles=[principle],
            content="class SourceAnnotator: pass",
            path="/tmp/source_annotator.py",
            parent_session_id="test-session",
        )

        self.assertIn('<exceptions principle="OCP">', prompt)
        self.assertIn("**Dependency-free units**", prompt)
        self.assertIn("**Pure data structures**", prompt)


if __name__ == "__main__":
    unittest.main()
