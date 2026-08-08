"""Defines conversion of MCP configuration into Codex CLI arguments."""

from typing import Protocol


"""
solid-name: CodexConfigArgumentBuilding
solid-category: abstraction
solid-description: Contract for translating health-session configuration into Codex command arguments.
solid-tags: [hook, llm]
"""
class CodexConfigArgumentBuilding(Protocol):
    def build(self, mcp_config: str) -> list[str]: ...
