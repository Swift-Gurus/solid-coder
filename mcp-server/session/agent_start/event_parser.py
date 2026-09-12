"""Parses agent-start hook input into a typed event."""

from typing import Optional, Protocol

from harness.flow_validation_error import FlowValidationError
from harness.json_loading import JsonLoading
from harness.structured_model_decoding import StructuredModelDecoding
from session.agent_start.event import AgentStartEvent


"""
solid-name: AgentStartEventParsing
solid-category: abstraction
solid-description: Contract for parsing typed agent-start hook events.
"""
class AgentStartEventParsing(Protocol):
    def parse(self, raw: str, default_cwd: str) -> Optional[AgentStartEvent]: ...


"""
solid-name: AgentStartEventParser
solid-category: service
solid-description: Coordinates agent-start JSON loading and typed event decoding.
"""
class AgentStartEventParser(AgentStartEventParsing):

    def __init__(
        self,
        json_loader: JsonLoading,
        event_decoder: StructuredModelDecoding[AgentStartEvent],
    ) -> None:
        self._json_loader = json_loader
        self._event_decoder = event_decoder

    def parse(
        self,
        raw: str,
        default_cwd: str,
    ) -> Optional[AgentStartEvent]:
        try:
            event = self._event_decoder.decode(
                self._json_loader.safe_load(raw),
                "agent-start event",
            )
        except (FlowValidationError, TypeError, ValueError):
            return None
        if event.cwd:
            return event
        return event.model_copy(update={"cwd": default_cwd})
