"""
solid-name: FlowInitializing
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for initializing a flow with specified parameters and isolation configuration.
"""

from __future__ import annotations

from typing import Protocol

from harness.flow_init import FlowInit


class FlowInitializing(Protocol):
    def initialize(self, flow: str, params: dict, isolated: bool) -> FlowInit: ...
