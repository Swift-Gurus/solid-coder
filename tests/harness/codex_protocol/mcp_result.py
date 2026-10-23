"""Defines the MCP response fields required by transcript assertions."""

from codex_protocol.output_text import CodexOutputText
from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: CodexMcpResult
solid-category: test-support
solid-description: Projects MCP response content and error status so echoed tool names cannot stand in for successful calls.
"""


class CodexMcpResult(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    content: list[CodexOutputText] = Field(min_length=1)
    is_error: bool = Field(default=False, alias="isError")
