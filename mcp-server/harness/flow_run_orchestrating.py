"""
solid-name: FlowRunOrchestrating
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for unified access to all flow run operations.
"""

from __future__ import annotations

from harness.active_run_lock_clearing import ActiveRunLockClearing
from harness.flow_starting import FlowStarting
from harness.flow_stepping import FlowStepping
from harness.flow_status_reading import FlowStatusReading


class FlowRunOrchestrating(FlowStarting, FlowStepping, FlowStatusReading, ActiveRunLockClearing):
    """Composed protocol providing all flow MCP operations."""
