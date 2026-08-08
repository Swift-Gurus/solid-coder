"""Defines one backend-neutral live integration-session request."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


"""
solid-name: LiveSessionRequest
solid-category: value
solid-description: Carries the prompt, model, timeout, project, plugin, MCP, and tool constraints required to launch one live integration session.
"""
@dataclass(frozen=True)
class LiveSessionRequest:

    prompt: str
    project_root: Path
    plugin_root: Path
    model: str
    timeout: int
    allowed_tools: str
    mcp_config: str
