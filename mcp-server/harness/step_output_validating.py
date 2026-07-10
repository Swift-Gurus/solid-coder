"""
solid-name: StepOutputValidating
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for validating step outputs against their declared specifications.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef, StepInstance


class StepOutputValidating(Protocol):

    def validate(
        self,
        ready: list[StepInstance],
        outputs: dict,
        flow_def: FlowDef,
    ) -> list[str]: ...