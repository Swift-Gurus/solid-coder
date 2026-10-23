"""Defines the typed invocation projection used by live protocol checks."""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field

"""
solid-name: CodexToolCallEvent
solid-category: test-support
solid-description: Carries a timestamped Codex tool invocation and its correlation identity without decoding workflow submissions.
"""


class CodexToolCallEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    timestamp: datetime
    event_type: Literal["response_item"] = Field(validation_alias="type")
    payload_type: Literal["custom_tool_call", "function_call"] = Field(
        validation_alias=AliasPath("payload", "type"),
    )
    call_id: str = Field(validation_alias=AliasPath("payload", "call_id"))
    name: str = Field(validation_alias=AliasPath("payload", "name"))
    input: str = Field(
        validation_alias=AliasChoices(
            AliasPath("payload", "input"),
            AliasPath("payload", "arguments"),
        )
    )
