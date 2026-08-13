"""
solid-name: test_step_graph_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests workflow-step identity, dependency, and dependency-cycle validation.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.directed_graph_factory import DirectedGraphFactory
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.include_alias_group import IncludeAliasGroup
from harness.incoming_edge_checker import IncomingEdgeChecker
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.models import FlowValidationError
from harness.step_declaration import StepDeclaration
from harness.step_dependency_graph_factory import StepDependencyGraphFactory
from harness.step_graph_validator import StepGraphValidator
from harness.step_identity_resolver import StepIdentityResolver
from harness.unique_step_identity_validator import UniqueStepIdentityValidator


def _make_validator() -> StepGraphValidator:
    error_factory = FlowValidationErrorFactory()
    identity_resolver = StepIdentityResolver(error_factory)
    return StepGraphValidator(
        identity_validator=UniqueStepIdentityValidator(
            identity_resolver,
            error_factory,
        ),
        graph_factory=StepDependencyGraphFactory(
            identity_resolver=identity_resolver,
            graph_factory=DirectedGraphFactory(),
            error_factory=error_factory,
        ),
        cycle_detector=KahnCycleDetector(IncomingEdgeChecker()),
        error_factory=error_factory,
    )


class TestStepGraphValidator(unittest.TestCase):
    def setUp(self):
        self.sut = _make_validator()

    def test_accepts_depends_on_naming_a_group_alias(self):
        steps = [StepDeclaration(id="reviewer", prompt="p", depends_on=["sub"])]

        self.sut.validate(
            steps,
            alias_groups=[
                IncludeAliasGroup(alias="sub", member_ids=["sub.step_a"])
            ],
        )

    def test_raises_on_unknown_dependency(self):
        steps = [StepDeclaration(id="a", prompt="p", depends_on=["nonexistent"])]

        with self.assertRaises(FlowValidationError):
            self.sut.validate(steps, alias_groups=[])


if __name__ == "__main__":
    unittest.main()
