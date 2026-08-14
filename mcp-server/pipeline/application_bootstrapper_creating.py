"""Defines construction of configured pipeline applications."""

from typing import Protocol

from message_transport_running import MessageTransportRunning


"""
solid-name: ApplicationBootstrapperCreating
solid-category: abstraction
solid-description: Contract for creating a configured pipeline application.
"""
class ApplicationBootstrapperCreating(Protocol):
    def make(self) -> MessageTransportRunning: ...
