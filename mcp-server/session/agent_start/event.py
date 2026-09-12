"""Defines typed input for an agent-start hook event."""

from pydantic import BaseModel


"""
solid-name: AgentStartEvent
solid-category: model
solid-description: Carries session identity and project context from an agent-start hook.
"""
class AgentStartEvent(BaseModel):
    session_id: str = ""
    cwd: str = ""
