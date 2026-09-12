"""Runs the agent-start hook from injected process boundaries."""

from harness.env_reading import EnvReading
from session.agent_start.current_directory import CurrentDirectoryReading
from session.agent_start.event_parser import AgentStartEventParsing
from session.agent_start.handler import AgentStartHandler
from session.agent_start.input_reader import AgentStartInputReading

_SESSION_TYPE_ENV = "SOLID_CODER_SESSION_TYPE"


"""
solid-name: AgentStartApplication
solid-category: service
solid-spec: [SPEC-049]
solid-description: Coordinates typed agent-start input with project and session registration.
"""
class AgentStartApplication:

    def __init__(
        self,
        input_reader: AgentStartInputReading,
        current_directory: CurrentDirectoryReading,
        environment: EnvReading,
        event_parser: AgentStartEventParsing,
        handler: AgentStartHandler,
    ) -> None:
        self._input_reader = input_reader
        self._current_directory = current_directory
        self._environment = environment
        self._event_parser = event_parser
        self._handler = handler

    def run(self) -> None:
        event = self._event_parser.parse(
            self._input_reader.read(),
            self._current_directory.read(),
        )
        if event is None:
            return
        self._handler.handle(
            event,
            self._environment.get(_SESSION_TYPE_ENV, "").strip(),
        )
