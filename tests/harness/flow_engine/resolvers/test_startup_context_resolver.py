"""
solid-name: test_startup_context_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests gathering base run directory and search paths into one context.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.startup_context_resolver import StartupContextResolver


class StubBaseDirResolver:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def resolve(self) -> Path:
        return self._base_dir


class StubSearchPaths:
    def __init__(self, paths: list[Path]) -> None:
        self._paths = paths

    def resolve(self) -> list[Path]:
        return self._paths


class TestStartupContextResolver(unittest.TestCase):

    def test_resolves_base_dir_and_stringified_search_paths(self):
        base_dir = Path("/runs")
        search_paths = [Path("/project/.solid-coder/harness/flows"), Path("/plugin/harness/flows")]
        sut = StartupContextResolver(
            base_dir_resolver=StubBaseDirResolver(base_dir),
            search_paths=StubSearchPaths(search_paths),
        )

        context = sut.resolve()

        self.assertEqual(context.base_dir, base_dir)
        self.assertEqual(context.search_paths, [str(p) for p in search_paths])


if __name__ == "__main__":
    unittest.main()
