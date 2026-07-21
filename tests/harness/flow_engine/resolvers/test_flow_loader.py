"""
solid-name: TestFlowLoader
solid-description: Validates the loading of flow configuration files and detection of structural errors.
solid-category: unit-test
"""

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_engine_assembly import build_default_assembly
from harness.models import FlowValidationError


class TestFlowLoader(unittest.TestCase):

    def setUp(self):
        self.assembly = build_default_assembly()
        self.loader = self.assembly.flow_loader
        self._tmpdir = tempfile.mkdtemp()

    def _write(self, name: str, content: str) -> str:
        path = str(Path(self._tmpdir) / name)
        Path(path).write_text(textwrap.dedent(content))
        return path

    def test_loads_minimal_valid_flow(self):
        path = self._write("flow.yaml", """
            name: my_flow
            max_turns: 5
            steps:
              - id: step_a
                prompt: Do something
        """)
        flow = self.loader.load(path, [])
        self.assertEqual(flow.name, "my_flow")
        self.assertEqual(flow.max_turns, 5)
        self.assertEqual(len(flow.steps), 1)
        self.assertEqual(flow.steps[0].id, "step_a")

    def test_raises_on_missing_file(self):
        with self.assertRaises(FlowValidationError):
            self.loader.load("/nonexistent/flow.yaml", [])

    def test_raises_on_duplicate_step_ids(self):
        path = self._write("dupe.yaml", """
            name: dupe
            steps:
              - id: a
                prompt: First
              - id: a
                prompt: Second
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])

    def test_raises_on_unknown_dependency(self):
        path = self._write("bad_dep.yaml", """
            name: bad
            steps:
              - id: a
                prompt: p
                depends_on: [nonexistent]
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])

    def test_raises_on_dependency_cycle(self):
        path = self._write("cycle.yaml", """
            name: cyclic
            steps:
              - id: a
                prompt: p
                depends_on: [b]
              - id: b
                prompt: p
                depends_on: [a]
        """)
        with self.assertRaises(FlowValidationError):
            self.loader.load(path, [])


if __name__ == "__main__":
    unittest.main()
