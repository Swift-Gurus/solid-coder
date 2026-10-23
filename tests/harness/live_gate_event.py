"""Combines existing flow event projections with submitting-session identity."""

from flow_audit_event import FlowAuditEvent
from harness.step_completed_event import StepCompletedEvent

"""
solid-name: LiveGateEvent
solid-category: test-support
solid-spec: [SPEC-036, SPEC-050]
solid-description: Reuses the flow event and completion contracts to distinguish engine operations from child-model submissions in a live gate audit.
"""


class LiveGateEvent(FlowAuditEvent, StepCompletedEvent):
    session_id: str = ""
