"""
solid-name: FlowRunOrchestrating
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for unified access to all flow run operations.
"""

from __future__ import annotations

from harness.flow_starting import FlowStarting
from harness.flow_stepping import FlowStepping
from harness.flow_status_reading import FlowStatusReading


class FlowRunOrchestrating(FlowStarting, FlowStepping, FlowStatusReading):
    """Composed protocol providing all three flow MCP operations."""
