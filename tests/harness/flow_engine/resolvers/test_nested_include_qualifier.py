"""Validates nested include qualification preserves typed runtime controls."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.include_alias_group import IncludeAliasGroup  # noqa: E402
from harness.include_resolution import IncludeResolution  # noqa: E402
from harness.nested_include_qualifier import NestedIncludeQualifier  # noqa: E402
from harness.step_output_reference import StepOutputReference  # noqa: E402
from harness.step_qualifier import StepQualifier  # noqa: E402
from harness.workflow_expression import WorkflowExpression  # noqa: E402
from harness.workflow_input_binding import WorkflowInputBinding  # noqa: E402


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
            for_each=StepOutputReference("prepare", "units"),
            input_bindings=[
                WorkflowInputBinding(
                    name="review_unit",
                    expression=WorkflowExpression("item"),
                )
            ],
            condition=condition,
        )
        sut = NestedIncludeQualifier(step_qualifier=StepQualifier())

        result = sut.qualify(
            "review",
            IncludeResolution(
                steps=[{"id": "rule.measure", "prompt": "Measure"}],
                alias_groups=[group],
            ),
        )

        self.assertEqual(
            result.alias_groups,
            [
                IncludeAliasGroup(
                    alias="review.rule",
                    member_ids=["review.rule.measure"],
                    depends_on=group.depends_on,
                    for_each=group.for_each,
                    input_bindings=group.input_bindings,
                    condition=condition,
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
