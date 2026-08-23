"""Provides the standard audited rule-step output declaration."""

from harness.output_spec import OutputSpec
from harness.rule_additional_info_output_providing import (
    RuleAdditionalInfoOutputProviding,
)


"""
solid-name: RuleAdditionalInfoOutputProvider
solid-category: service
solid-spec: [SPEC-039]
solid-description: Supplies the required reasoning-and-evidence output contract shared by metric and exception steps.
"""
class RuleAdditionalInfoOutputProvider(RuleAdditionalInfoOutputProviding):
    def provide(self) -> OutputSpec:
        return OutputSpec(
            name="additional_info",
            type="data",
            schema={
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string", "minLength": 1},
                    "evidence": {"type": "string", "minLength": 1},
                },
                "required": ["reasoning", "evidence"],
                "additionalProperties": False,
            },
        )
