"""Defines supported isolated-session MCP configurations."""

from enum import Enum


"""
solid-name: McpConfigProfile
solid-category: model
solid-spec: [SPEC-036]
solid-description: Identifies the supported MCP capability sets for isolated model sessions.
"""
class McpConfigProfile(str, Enum):
    LEGACY_HEALTH = "legacy-health"
    GATE_FLOW = "gate-flow"
