"""Defines the typed MCP tool-completion projection of a Codex transcript event."""

from datetime import datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field


"""
solid-name: CodexTranscriptToolCompletionEvent
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Decodes a completed MCP tool identity, result text, and timestamp for review-stage boundary detection.
"""
class CodexTranscriptToolCompletionEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    timestamp: datetime
    event_type: Literal["event_msg"] = Field(
        validation_alias="type",
    )
    payload_type: Literal["mcp_tool_call_end"] = Field(
        validation_alias=AliasPath("payload", "type"),
    )
    tool: str = Field(
        min_length=1,
        validation_alias=AliasPath("payload", "invocation", "tool"),
    )
    result_text: str = Field(
        validation_alias=AliasPath(
            "payload",
            "result",
            "Ok",
            "content",
            0,
            "text",
        ),
    )
