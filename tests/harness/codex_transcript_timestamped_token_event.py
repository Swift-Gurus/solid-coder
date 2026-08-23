"""Defines the timestamped token projection of a Codex transcript event."""

from datetime import datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field

from codex_token_usage import CodexTokenUsage


"""
solid-name: CodexTranscriptTimestampedTokenEvent
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Decodes cumulative token usage and its timestamp for comparison-stage accounting.
"""
class CodexTranscriptTimestampedTokenEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    timestamp: datetime
    event_type: Literal["event_msg"] = Field(
        validation_alias="type",
    )
    payload_type: Literal["token_count"] = Field(
        validation_alias=AliasPath("payload", "type"),
    )
    token_usage: CodexTokenUsage = Field(
        validation_alias=AliasPath(
            "payload",
            "info",
            "total_token_usage",
        ),
    )
