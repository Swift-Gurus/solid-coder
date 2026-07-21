"""
solid-name: test_name_resolving_flow_loader
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests that the decorator resolves a flow name before delegating to the inner loader.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef
from harness.name_resolving_flow_loader import NameResolvingFlowLoader


class StubFileResolver:
    def __init__(self, resolved: str) -> None:
        self._resolved = resolved
        self.calls: list[tuple] = []

    def resolve(self, flow: str, search_paths: list[str]) -> str:
        self.calls.append((flow, search_paths))
        return self._resolved


class StubInnerLoader:
    def __init__(self, flow_def: FlowDef) -> None:
        self._flow_def = flow_def
        self.calls: list[tuple] = []

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        self.calls.append((path, search_paths))
        return self._flow_def


class TestNameResolvingFlowLoader(unittest.TestCase):

    def test_loads_using_the_resolved_path(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        file_resolver = StubFileResolver(resolved="/resolved/code_review.yaml")
        inner_loader = StubInnerLoader(flow_def)
        sut = NameResolvingFlowLoader(file_resolver=file_resolver, inner_loader=inner_loader)

        result = sut.load("code_review", ["/search/dir"])

        self.assertIs(result, flow_def)
        self.assertEqual(file_resolver.calls, [("code_review", ["/search/dir"])])
        self.assertEqual(inner_loader.calls, [("/resolved/code_review.yaml", ["/search/dir"])])


if __name__ == "__main__":
    unittest.main()
