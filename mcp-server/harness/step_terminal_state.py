"""Defines terminal workflow-step states used by result publication."""

from enum import Enum


"""
solid-name: StepTerminalState
solid-category: model
solid-spec: [SPEC-037]
solid-description: Enumerates pending, completed, and skipped workflow-step states.
"""
class StepTerminalState(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
