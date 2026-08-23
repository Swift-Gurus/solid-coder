"""
solid-description: Provides output sizing configuration for MCP tools.
solid-category: utility
solid-tags: [utility]
"""

LARGE_OUTPUT: dict = {"anthropic/maxResultSizeChars": 1_000_000}
COMPLETE_FLOW_OUTPUT: dict = {"anthropic/maxResultSizeChars": 4_000_000}
