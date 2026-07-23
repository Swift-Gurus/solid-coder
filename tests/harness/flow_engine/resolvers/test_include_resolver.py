"""
solid-name: test_include_resolver
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests inlining included sub-flow steps under an alias, qualifying IDs, rewriting intra-group sibling references, and detecting circular includes.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.include_resolver import IncludeResolver
from harness.models import FlowValidationError


class StubFileLoader:
    def __init__(self, files: dict[str, dict]) -> None:
        self._files = files

    def load(self, path: Path):
        return self._files.get(str(path))


class TestIncludeResolver(unittest.TestCase):

    def test_qualifies_included_step_ids_with_alias(self):
        sub_flow_path = str(Path("/flows/sub.yaml"))
        loader = StubFileLoader({sub_flow_path: {"steps": [{"id": "step_a", "prompt": "p"}]}})
        sut = IncludeResolver(file_loader=loader)

        result = sut.resolve([{"include": "sub.yaml", "as": "foo"}], "/flows/parent.yaml")

        self.assertEqual([s["id"] for s in result.steps], ["foo.step_a"])
        self.assertEqual(result.alias_groups, {"foo": ["foo.step_a"]})

    def test_includes_same_sub_flow_twice_under_distinct_aliases_without_collision(self):
        sub_flow_path = str(Path("/flows/sub.yaml"))
        loader = StubFileLoader({sub_flow_path: {"steps": [{"id": "step_a", "prompt": "p"}]}})
        sut = IncludeResolver(file_loader=loader)

        result = sut.resolve(
            [
                {"include": "sub.yaml", "as": "foo"},
                {"include": "sub.yaml", "as": "bar"},
            ],
            "/flows/parent.yaml",
        )

        self.assertEqual(sorted(s["id"] for s in result.steps), ["bar.step_a", "foo.step_a"])
        self.assertEqual(result.alias_groups, {"foo": ["foo.step_a"], "bar": ["bar.step_a"]})

    def test_rewrites_unqualified_sibling_dependency_within_group(self):
        sub_flow_path = str(Path("/flows/sub.yaml"))
        loader = StubFileLoader({sub_flow_path: {"steps": [
            {"id": "step_a", "prompt": "p"},
            {"id": "step_b", "prompt": "p", "depends_on": ["step_a"]},
        ]}})
        sut = IncludeResolver(file_loader=loader)

        result = sut.resolve([{"include": "sub.yaml", "as": "foo"}], "/flows/parent.yaml")

        step_b = next(s for s in result.steps if s["id"] == "foo.step_b")
        self.assertEqual(step_b["depends_on"], ["foo.step_a"])

    def test_leaves_top_level_step_depends_on_untouched(self):
        steps = [{"id": "top", "prompt": "p", "depends_on": ["other_top"]}]
        sut = IncludeResolver(file_loader=StubFileLoader({}))

        result = sut.resolve(steps, "/flows/parent.yaml")

        self.assertEqual(result.steps, steps)

    def test_raises_on_unresolvable_include(self):
        sut = IncludeResolver(file_loader=StubFileLoader({}))

        with self.assertRaises(FlowValidationError):
            sut.resolve([{"include": "missing.yaml", "as": "foo"}], "/flows/parent.yaml")

    def test_supports_transitive_includes(self):
        inner_path = str(Path("/flows/inner.yaml"))
        outer_path = str(Path("/flows/outer.yaml"))
        loader = StubFileLoader({
            outer_path: {"steps": [{"include": "inner.yaml", "as": "inner"}]},
            inner_path: {"steps": [{"id": "leaf", "prompt": "p"}]},
        })
        sut = IncludeResolver(file_loader=loader)

        result = sut.resolve([{"include": "outer.yaml", "as": "outer"}], "/flows/parent.yaml")

        self.assertEqual([s["id"] for s in result.steps], ["outer.inner.leaf"])

    def test_raises_on_self_including_flow(self):
        cyclic_path = str(Path("/flows/cyclic.yaml"))
        loader = StubFileLoader({
            cyclic_path: {"steps": [{"include": "cyclic.yaml", "as": "again"}]},
        })
        sut = IncludeResolver(file_loader=loader)

        with self.assertRaises(FlowValidationError):
            sut.resolve([{"include": "cyclic.yaml", "as": "first"}], "/flows/parent.yaml")

    def test_qualifies_inline_group_step_ids_with_two_steps(self):
        sut = IncludeResolver(file_loader=StubFileLoader({}))

        result = sut.resolve(
            [{"group": "review", "steps": [
                {"id": "draft", "prompt": "p"},
                {"id": "approve", "prompt": "p", "depends_on": ["draft"]},
            ]}],
            "/flows/parent.yaml",
        )

        self.assertEqual(sorted(s["id"] for s in result.steps), ["review.approve", "review.draft"])
        self.assertEqual(sorted(result.alias_groups["review"]), ["review.approve", "review.draft"])

    def test_rewrites_unqualified_sibling_dependency_within_inline_group(self):
        sut = IncludeResolver(file_loader=StubFileLoader({}))

        result = sut.resolve(
            [{"group": "review", "steps": [
                {"id": "draft", "prompt": "p"},
                {"id": "approve", "prompt": "p", "depends_on": ["draft"]},
            ]}],
            "/flows/parent.yaml",
        )

        approve = next(s for s in result.steps if s["id"] == "review.approve")
        self.assertEqual(approve["depends_on"], ["review.draft"])

    def test_inline_group_leaves_external_dependency_untouched(self):
        sut = IncludeResolver(file_loader=StubFileLoader({}))

        result = sut.resolve(
            [{"group": "review", "steps": [
                {"id": "draft", "prompt": "p", "depends_on": ["outside_step"]},
            ]}],
            "/flows/parent.yaml",
        )

        draft = next(s for s in result.steps if s["id"] == "review.draft")
        self.assertEqual(draft["depends_on"], ["outside_step"])

    def test_raises_on_empty_inline_group_steps(self):
        sut = IncludeResolver(file_loader=StubFileLoader({}))

        with self.assertRaises(FlowValidationError):
            sut.resolve([{"group": "review", "steps": []}], "/flows/parent.yaml")

    def test_inline_group_and_file_include_can_coexist(self):
        sub_flow_path = str(Path("/flows/sub.yaml"))
        loader = StubFileLoader({sub_flow_path: {"steps": [{"id": "step_a", "prompt": "p"}]}})
        sut = IncludeResolver(file_loader=loader)

        result = sut.resolve(
            [
                {"include": "sub.yaml", "as": "foo"},
                {"group": "bar", "steps": [{"id": "step_b", "prompt": "p"}]},
            ],
            "/flows/parent.yaml",
        )

        self.assertEqual(sorted(s["id"] for s in result.steps), ["bar.step_b", "foo.step_a"])
        self.assertEqual(result.alias_groups, {"foo": ["foo.step_a"], "bar": ["bar.step_b"]})


if __name__ == "__main__":
    unittest.main()
