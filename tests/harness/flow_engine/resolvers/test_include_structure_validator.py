"""
solid-name: test_include_structure_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests include-alias collisions, group opacity, and circular include validation.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.directed_graph_factory import DirectedGraphFactory
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.include_alias_collision_validator import IncludeAliasCollisionValidator
from harness.include_alias_group import IncludeAliasGroup
from harness.include_cycle_validator import IncludeCycleValidator
from harness.include_group_membership_resolver import IncludeGroupMembershipResolver
from harness.include_group_opacity_validator import IncludeGroupOpacityValidator
from harness.include_structure_validator import IncludeStructureValidator
from harness.incoming_edge_checker import IncomingEdgeChecker
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.models import FlowValidationError
from harness.step_declaration import StepDeclaration


class TestIncludeStructureValidator(unittest.TestCase):
    def setUp(self):
        error_factory = FlowValidationErrorFactory()
        self.sut = IncludeStructureValidator(
            alias_collision_validator=IncludeAliasCollisionValidator(error_factory),
            group_opacity_validator=IncludeGroupOpacityValidator(
                membership_resolver=IncludeGroupMembershipResolver(),
                error_factory=error_factory,
            ),
            include_cycle_validator=IncludeCycleValidator(
                graph_factory=DirectedGraphFactory(),
                cycle_detector=KahnCycleDetector(IncomingEdgeChecker()),
                error_factory=error_factory,
            ),
        )

    def test_raises_when_alias_collides_with_existing_step_id(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate_includes(
                steps=[],
                alias_groups=[
                    IncludeAliasGroup(
                        alias="reviewer",
                        member_ids=["reviewer.step_a"],
                    )
                ],
                top_level_step_ids={"reviewer"},
                include_chain=[],
            )

    def test_raises_on_circular_include_chain(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate_includes(
                steps=[],
                alias_groups=[],
                top_level_step_ids=set(),
                include_chain=["flow_a.yaml", "flow_b.yaml", "flow_a.yaml"],
            )

    def test_accepts_a_non_circular_include_chain(self):
        self.sut.validate_includes(
            steps=[],
            alias_groups=[],
            top_level_step_ids=set(),
            include_chain=["flow_a.yaml", "flow_b.yaml"],
        )

    def test_raises_when_step_outside_group_depends_on_qualified_reference(self):
        steps = [
            StepDeclaration(id="outside", prompt="p", depends_on=["sub.step_a"]),
            StepDeclaration(id="sub.step_a", prompt="p"),
        ]

        with self.assertRaises(FlowValidationError):
            self.sut.validate_includes(
                steps=steps,
                alias_groups=[
                    IncludeAliasGroup(alias="sub", member_ids=["sub.step_a"])
                ],
                top_level_step_ids={"outside"},
                include_chain=[],
            )

    def test_allows_member_step_to_depend_on_qualified_sibling(self):
        steps = [
            StepDeclaration(id="sub.step_a", prompt="p"),
            StepDeclaration(
                id="sub.step_b",
                prompt="p",
                depends_on=["sub.step_a"],
            ),
        ]

        self.sut.validate_includes(
            steps=steps,
            alias_groups=[
                IncludeAliasGroup(
                    alias="sub",
                    member_ids=["sub.step_a", "sub.step_b"],
                )
            ],
            top_level_step_ids=set(),
            include_chain=[],
        )

    def test_allows_outer_group_member_to_depend_on_nested_group_member(self):
        steps = [
            StepDeclaration(
                id="first.verify",
                prompt="p",
                depends_on=["first.process.execute"],
            ),
            StepDeclaration(id="first.process.execute", prompt="p"),
        ]

        self.sut.validate_includes(
            steps=steps,
            alias_groups=[
                IncludeAliasGroup(
                    alias="first",
                    member_ids=["first.verify", "first.process.execute"],
                ),
                IncludeAliasGroup(
                    alias="first.process",
                    member_ids=["first.process.execute"],
                ),
            ],
            top_level_step_ids=set(),
            include_chain=[],
        )


if __name__ == "__main__":
    unittest.main()
