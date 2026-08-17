"""Tests typed dependency resolution for included workflow instances."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.include_alias_group import IncludeAliasGroup
from harness.included_workflow_dependencies_resolver import (
    IncludedWorkflowDependenciesResolver,
)
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity
from harness.models import StepDef


"""
solid-name: TestIncludedWorkflowDependenciesResolver
solid-category: unit-test
solid-spec: [SPEC-037]
solid-description: Verifies child dependencies resolve through typed identities whose execution values have no parseable naming convention.
"""
class TestIncludedWorkflowDependenciesResolver(unittest.TestCase):

    def test_resolves_internal_dependency_to_opaque_execution_identity(self) -> None:
        identities = IncludedWorkflowStepIdentities(
            entries=[
                IncludedWorkflowStepIdentity(
                    declaration_id="review.inspect",
                    local_step_id="inspect",
                    execution_step_id="opaque-execution-a7f4",
                ),
                IncludedWorkflowStepIdentity(
                    declaration_id="review.report",
                    local_step_id="report",
                    execution_step_id="opaque-execution-b9c2",
                ),
            ]
        )
        group = IncludeAliasGroup(
            alias="review",
            member_ids=["review.inspect", "review.report"],
            depends_on=["prepare"],
        )
        report = StepDef(
            id="review.report",
            prompt="Report",
            depends_on=["review.inspect"],
        )

        dependencies = IncludedWorkflowDependenciesResolver().resolve(
            report,
            group,
            identities,
        )

        self.assertEqual(dependencies, ["opaque-execution-a7f4"])


if __name__ == "__main__":
    unittest.main()
