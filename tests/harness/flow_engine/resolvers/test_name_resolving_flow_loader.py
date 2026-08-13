"""
solid-name: test_name_resolving_flow_loader
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests that the decorator resolves a flow name before delegating to the inner loader.
"""

from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef
from harness.name_resolving_flow_loader import NameResolvingFlowLoader


class StubFileResolver:
    def __init__(self, resolved: str, events: list[str]) -> None:
        self._resolved = resolved
        self._events = events
        self.calls: list[tuple] = []

    def resolve(self, flow: str, search_paths: list[str]) -> str:
        self._events.append("file-resolved")
        self.calls.append((flow, search_paths))
        return self._resolved


class StubInnerLoader:
    def __init__(self, flow_def: FlowDef, events: list[str]) -> None:
        self._flow_def = flow_def
        self._events = events
        self.calls: list[tuple] = []

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        self._events.append("definition-loaded")
        self.calls.append((path, search_paths))
        return self._flow_def


class StubCatalogScope:
    def __init__(self, events: list[str]) -> None:
        self._events = events
        self.calls: list[list[str]] = []

    @contextmanager
    def scope(self, search_paths: list[str]) -> Iterator[None]:
        self.calls.append(search_paths)
        self._events.append("scope-entered")
        try:
            yield
        finally:
            self._events.append("scope-exited")


class TestNameResolvingFlowLoader(unittest.TestCase):

    def test_loads_using_the_resolved_path(self):
        events: list[str] = []
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        file_resolver = StubFileResolver(resolved="/resolved/code_review.yaml", events=events)
        inner_loader = StubInnerLoader(flow_def, events=events)
        catalog_scope = StubCatalogScope(events=events)
        sut = NameResolvingFlowLoader(
            file_resolver=file_resolver,
            inner_loader=inner_loader,
            catalog_scope=catalog_scope,
        )

        result = sut.load("code_review", ["/search/dir"])

        self.assertIs(result, flow_def)
        self.assertEqual(catalog_scope.calls, [["/search/dir"]])
        self.assertEqual(file_resolver.calls, [("code_review", ["/search/dir"])])
        self.assertEqual(inner_loader.calls, [("/resolved/code_review.yaml", ["/search/dir"])])
        self.assertEqual(events, ["scope-entered", "file-resolved", "definition-loaded", "scope-exited"])


if __name__ == "__main__":
    unittest.main()
