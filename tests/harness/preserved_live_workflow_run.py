"""Defines a completed live workflow session and its preserved canonical run."""

from dataclasses import dataclass
from pathlib import Path

from live_session_result import LiveSessionResult


"""
solid-name: PreservedLiveWorkflowRun
solid-category: value
solid-description: Carries the model session result and recursively preserved MCP run directory for E2E assertions.
"""
@dataclass(frozen=True)
class PreservedLiveWorkflowRun:
    session: LiveSessionResult
    run_directory: Path
