"""Defines construction of the flow-run orchestration service."""

from typing import Protocol

from harness.flow_run_orchestrating import FlowRunOrchestrating
from message_transport_running import MessageTransportRunning


"""
solid-name: FlowRunCreating
solid-category: abstraction
solid-description: Contract for creating flow-run orchestration for one message transport.
"""
class FlowRunCreating(Protocol):
    def create(self, transport: MessageTransportRunning) -> FlowRunOrchestrating: ...
