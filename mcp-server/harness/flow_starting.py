"""
solid-name: FlowStarting
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for starting a flow run and providing its initial execution state.
"""

from __future__ import annotations

from typing import Protocol

from harness.flow_start_result import FlowStartResult


class FlowStarting(Protocol):

    def flow_start(self, flow: str, params: dict | None = None) -> FlowStartResult: ...
