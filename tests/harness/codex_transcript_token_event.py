"""Defines the typed token-count projection of one Codex transcript event."""

from codex_token_usage import CodexTokenUsage
from pydantic import AliasPath, BaseModel, ConfigDict, Field

"""
solid-name: CodexTranscriptTokenEvent
solid-category: test-support
solid-spec: [SPEC-036, SPEC-041]
solid-description: Decodes only the nested event kind and cumulative usage fields required by comparison evidence.
"""


class CodexTranscriptTokenEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    event_type: str | None = Field(
        default=None,
        validation_alias=AliasPath("payload", "type"),
    )
    total_usage: CodexTokenUsage | None = Field(
        default=None,
        validation_alias=AliasPath(
            "payload",
            "info",
            "total_token_usage",
        ),
    )
