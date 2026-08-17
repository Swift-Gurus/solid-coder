"""Defines common audit values for effective rule enablement."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: RuleEnablementDecision
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records authored and effective enablement values for one enrolled review rule.
"""
class RuleEnablementDecision(BaseModel):
    model_config = ConfigDict(frozen=True)

    authored_default: bool = True
    effective: bool
