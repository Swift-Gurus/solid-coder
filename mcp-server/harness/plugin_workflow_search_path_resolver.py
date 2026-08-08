"""Provides plugin-owned workflow search directories."""

from __future__ import annotations

from pathlib import Path

from harness.flow_search_path_resolving import FlowSearchPathResolving


"""
solid-name: PluginWorkflowSearchPathResolver
solid-category: service
solid-spec: [SPEC-031, SPEC-035]
solid-description: Resolves ordered package and legacy workflow search directories owned by the active plugin checkout.
"""
class PluginWorkflowSearchPathResolver(FlowSearchPathResolving):

    def __init__(self, plugin_root: Path) -> None:
        self._plugin_root = plugin_root

    def resolve(self) -> list[Path]:
        return [
            self._plugin_root / "workflows",
            self._plugin_root / "mcp-server" / "harness" / "flows",
        ]
