"""Validates nested include qualification preserves typed runtime controls."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.combined_rule_presentation import CombinedRulePresentation
from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.for_each_declaration import ForEachDeclaration
from harness.include_alias_group import IncludeAliasGroup
from harness.include_resolution import IncludeResolution
from harness.local_nested_identity_qualifier import (
    LocalNestedIdentityQualifier,
)
from harness.nested_include_alias_group_qualifier import (
    NestedIncludeAliasGroupQualifier,
)
from harness.nested_include_qualifier import NestedIncludeQualifier
from harness.step_output_reference import StepOutputReference
from harness.step_qualifier import StepQualifier
from harness.workflow_expression import WorkflowExpression
from harness.workflow_input_binding import WorkflowInputBinding


class TestNestedIncludeQualifier(unittest.TestCase):
    def test_preserves_nested_group_runtime_controls(self) -> None:
        condition = ComparisonCondition(
            reference=WorkflowExpression("params.review_unit.file_extension"),
            operator=ConditionOperator.EQUALS,
            expected=".swift",
        )
        group = IncludeAliasGroup(
            alias="rule",
            member_ids=["rule.measure"],
            depends_on=["prepare"],
            for_each=ForEachDeclaration(
                source=StepOutputReference("prepare", "units"),
            ),
            input_bindings=[
                WorkflowInputBinding(
                    name="review_unit",
                    expression=WorkflowExpression("item"),
                )
            ],
            condition=condition,
            combined_presentation=CombinedRulePresentation(
                group_alias="combined_reviews",
                rule_alias="srp",
            ),
        )
        sut = NestedIncludeQualifier(
            step_qualifier=StepQualifier(metric_source_qualifier=Mock()),
            group_qualifier=NestedIncludeAliasGroupQualifier(
                identity=LocalNestedIdentityQualifier()
            ),
        )

        result = sut.qualify(
            "review",
            IncludeResolution(
                steps=[
                    {"id": "prepare", "prompt": "Prepare"},
                    {"id": "rule.measure", "prompt": "Measure"},
                ],
                alias_groups=[group],
            ),
        )

        self.assertEqual(
            result.alias_groups,
            [
                IncludeAliasGroup(
                    alias="review.rule",
                    member_ids=["review.rule.measure"],
                    authored_alias="rule",
                    depends_on=["review.prepare"],
                    for_each=group.for_each,
                    input_bindings=group.input_bindings,
                    condition=condition,
                    combined_presentation=CombinedRulePresentation(
                        group_alias="review.combined_reviews",
                        rule_alias="srp",
                    ),
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
