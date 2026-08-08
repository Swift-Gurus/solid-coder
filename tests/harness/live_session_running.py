"""Defines live integration-session execution."""

from typing import Protocol

from live_session_request import LiveSessionRequest
from live_session_result import LiveSessionResult


"""
solid-name: LiveSessionRunning
solid-category: abstraction
solid-description: Contract for launching one model-backed live integration session and returning its final response.
"""
class LiveSessionRunning(Protocol):

    def run(self, request: LiveSessionRequest) -> LiveSessionResult: ...
