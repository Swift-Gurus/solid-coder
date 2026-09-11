"""Declares aggregate-step eligibility checking."""

from __future__ import annotations

from typing import Protocol

from harness.flow_def import FlowDef
from harness.step_def import StepDef
from harness.step_instance import StepInstance


"""
solid-name: AggregateStepEligibilityChecking
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for deciding whether a ready model step belongs to aggregate execution.
"""
class AggregateStepEligibilityChecking(Protocol):
    def is_eligible(
        self,
        flow: FlowDef,
        instance: StepInstance,
        step: StepDef,
    ) -> bool: ...
