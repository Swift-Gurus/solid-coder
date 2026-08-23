"""Defines the typed user-prompt projection of a Codex transcript event."""

from datetime import datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field


"""
solid-name: CodexTranscriptPromptEvent
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Decodes the timestamp and first user prompt text needed to locate the beginning of a review stage.
"""
class CodexTranscriptPromptEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    timestamp: datetime
    event_type: Literal["response_item"] = Field(
        validation_alias="type",
    )
    payload_type: Literal["message"] = Field(
        validation_alias=AliasPath("payload", "type"),
    )
    role: Literal["user"] = Field(
        validation_alias=AliasPath("payload", "role"),
    )
    prompt: str = Field(
        min_length=1,
        validation_alias=AliasPath("payload", "content", 0, "text"),
    )
