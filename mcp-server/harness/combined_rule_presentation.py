"""Defines typed ownership for one combined rule-presentation section."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: CombinedRulePresentation
solid-category: model
solid-spec: [SPEC-043]
solid-description: Identifies the enclosing combined group and authored child-rule alias carried through materialization and replay.
"""
class CombinedRulePresentation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    group_alias: str
    rule_alias: str
