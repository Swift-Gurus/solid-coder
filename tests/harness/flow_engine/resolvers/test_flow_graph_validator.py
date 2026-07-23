"""
solid-name: test_flow_graph_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests validating include-alias collisions, group opacity, circular includes, and dependencies on group aliases.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_graph_validator import FlowGraphValidator
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.include_structure_validator import IncludeStructureValidator
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.models import FlowValidationError
from harness.step_graph_validator import StepGraphValidator


def _make_flow_graph_validator() -> FlowGraphValidator:
    cycle_detector = KahnCycleDetector()
    return FlowGraphValidator(
        step_graph_validator=StepGraphValidator(cycle_detector=cycle_detector),
        include_structure_validator=IncludeStructureValidator(cycle_detector=cycle_detector),
        for_each_validator=ForEachReferenceValidator(),
    )


class TestFlowGraphValidatorRawWithAliases(unittest.TestCase):

    def setUp(self):
        self.sut = _make_flow_graph_validator()

    def test_accepts_depends_on_naming_a_group_alias(self):
        steps = [
            {"id": "reviewer", "prompt": "p", "depends_on": ["sub"]},
        ]
        self.sut.validate_raw(steps, alias_groups={"sub": ["sub.step_a"]})

    def test_still_raises_on_unknown_dependency(self):
        steps = [{"id": "a", "prompt": "p", "depends_on": ["nonexistent"]}]
        with self.assertRaises(FlowValidationError):
            self.sut.validate_raw(steps, alias_groups={})


class TestFlowGraphValidatorIncludes(unittest.TestCase):

    def setUp(self):
        self.sut = _make_flow_graph_validator()

    def test_raises_when_alias_collides_with_existing_step_id(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate_includes(
                steps=[],
                alias_groups={"reviewer": ["reviewer.step_a"]},
                top_level_step_ids={"reviewer"},
                include_chain=[],
            )

    def test_raises_on_circular_include_chain(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate_includes(
                steps=[],
                alias_groups={},
                top_level_step_ids=set(),
                include_chain=["flow_a.yaml", "flow_b.yaml", "flow_a.yaml"],
            )

    def test_accepts_a_non_circular_include_chain(self):
        self.sut.validate_includes(
            steps=[],
            alias_groups={},
            top_level_step_ids=set(),
            include_chain=["flow_a.yaml", "flow_b.yaml"],
        )

    def test_raises_when_step_outside_group_depends_on_qualified_reference(self):
        steps = [
            {"id": "outside", "prompt": "p", "depends_on": ["sub.step_a"]},
            {"id": "sub.step_a", "prompt": "p"},
        ]
        with self.assertRaises(FlowValidationError):
            self.sut.validate_includes(
                steps=steps,
                alias_groups={"sub": ["sub.step_a"]},
                top_level_step_ids={"outside"},
                include_chain=[],
            )

    def test_allows_member_step_to_depend_on_qualified_sibling_within_its_own_group(self):
        steps = [
            {"id": "sub.step_a", "prompt": "p"},
            {"id": "sub.step_b", "prompt": "p", "depends_on": ["sub.step_a"]},
        ]
        self.sut.validate_includes(
            steps=steps,
            alias_groups={"sub": ["sub.step_a", "sub.step_b"]},
            top_level_step_ids=set(),
            include_chain=[],
        )


if __name__ == "__main__":
    unittest.main()
