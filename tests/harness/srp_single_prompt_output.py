"""Defines the complete typed result of the single-prompt SRP experiment."""

from pydantic import BaseModel, ConfigDict

from harness.rule_exception_decision import RuleExceptionDecision
from srp_single_prompt_measurement import SRPSinglePromptMeasurement


"""
solid-name: SRPSinglePromptOutput
solid-category: test-support
solid-spec: [SPEC-036]
solid-description: Maps all three audited SRP measurements and the exception decision from one aggregate model submission.
"""
class SRPSinglePromptOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    verb_count: SRPSinglePromptMeasurement
    cohesion_groups: SRPSinglePromptMeasurement
    stakeholder_count: SRPSinglePromptMeasurement
    exception: RuleExceptionDecision
