"""
solid-name: McpRequestContextSessionReader
solid-category: service
solid-spec: [SPEC-013]
solid-description: Reads the current request's session identifier.
"""

from __future__ import annotations


class McpRequestContextSessionReader:

    def read_session_id(self) -> str:
        return ""
