"""Defines the typed token-count projection of one Codex transcript event."""

from typing import Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field

from codex_token_usage import CodexTokenUsage


"""
solid-name: CodexTranscriptTokenEvent
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Decodes only the nested event kind and cumulative usage fields required by comparison evidence.
"""
class CodexTranscriptTokenEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    event_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasPath("payload", "type"),
    )
    total_usage: Optional[CodexTokenUsage] = Field(
        default=None,
        validation_alias=AliasPath(
            "payload",
            "info",
            "total_token_usage",
        ),
    )
