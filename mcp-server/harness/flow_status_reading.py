"""
solid-name: FlowStatusReading
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for reading flow run status without side effects.
"""

from __future__ import annotations

from typing import Protocol

from harness.flow_status_result import FlowStatusResult


class FlowStatusReading(Protocol):

    def flow_status(self, run_id: str | None = None) -> FlowStatusResult: ...
