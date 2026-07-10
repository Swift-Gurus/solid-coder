"""
solid-name: FlowStepping
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for submitting step outputs and receiving the next ready steps or terminal status.
"""

from __future__ import annotations

from typing import Protocol

from harness.flow_next_result import FlowNextResult


class FlowStepping(Protocol):

    def flow_next(self, outputs: dict | None = None) -> FlowNextResult: ...
