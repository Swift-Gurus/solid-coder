"""
solid-name: test_group_dependency_expander
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests expanding a depends_on entry naming a group alias into dependencies on every member of that group.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.group_dependency_expander import GroupDependencyExpander
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_finder import IncludeAliasGroupFinder
from harness.step_declaration import StepDeclaration


class TestGroupDependencyExpander(unittest.TestCase):

    def setUp(self):
        self.sut = GroupDependencyExpander(IncludeAliasGroupFinder())

    def test_expands_alias_dependency_into_every_group_member(self):
        steps = [StepDeclaration(id="reviewer", prompt="p", depends_on=["sub"])]

        expanded = self.sut.expand(
            steps,
            alias_groups=[
                IncludeAliasGroup(
                    alias="sub",
                    member_ids=["sub.step_a", "sub.step_b"],
                )
            ],
        )

        self.assertEqual(expanded[0].depends_on, ["sub.step_a", "sub.step_b"])

    def test_leaves_unqualified_step_dependency_unchanged(self):
        steps = [StepDeclaration(id="b", prompt="p", depends_on=["a"])]

        expanded = self.sut.expand(
            steps,
            alias_groups=[
                IncludeAliasGroup(alias="sub", member_ids=["sub.step_a"])
            ],
        )

        self.assertEqual(expanded[0].depends_on, ["a"])

    def test_leaves_step_without_depends_on_untouched(self):
        steps = [StepDeclaration(id="a", prompt="p")]

        expanded = self.sut.expand(steps, alias_groups=[])

        self.assertEqual(expanded, steps)


if __name__ == "__main__":
    unittest.main()
