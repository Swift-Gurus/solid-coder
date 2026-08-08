"""
solid-name: FlowResultRendering
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for rendering flow results to string representations.
"""

from __future__ import annotations

from typing import Protocol

from harness.flow_next_result import FlowNextResult
from harness.flow_start_result import FlowStartResult


class FlowResultRendering(Protocol):

    def render_start(self, result: FlowStartResult) -> str: ...

    def render_next(self, result: FlowNextResult) -> str: ...