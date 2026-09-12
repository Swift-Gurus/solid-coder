"""Coordinates session registration for agent-start events."""

from pathlib import Path

from session.agent_start.event import AgentStartEvent
from session.project_context import SessionProjectDirectoryRecording
from session.session_registry import SessionRegistering


"""
solid-name: AgentStartHandler
solid-category: service
solid-spec: [SPEC-049]
solid-description: Records agent project context and registers managed session types.
"""
class AgentStartHandler:

    def __init__(
        self,
        project_directory_recorder: SessionProjectDirectoryRecording,
        session_registrar: SessionRegistering,
    ) -> None:
        self._project_directory_recorder = project_directory_recorder
        self._session_registrar = session_registrar

    def handle(
        self,
        event: AgentStartEvent,
        session_type: str,
    ) -> None:
        if not event.session_id:
            return
        self._project_directory_recorder.record(
            event.session_id,
            Path(event.cwd),
        )
        if session_type:
            self._session_registrar.register(
                session_id=event.session_id,
                session_type=session_type,
                cwd=event.cwd,
            )
