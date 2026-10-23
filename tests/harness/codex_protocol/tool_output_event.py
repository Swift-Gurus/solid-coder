"""Defines the typed response projection used by live protocol checks."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from codex_protocol.output_text import CodexOutputText
from pydantic import AliasPath, BaseModel, ConfigDict, Field

"""
solid-name: CodexToolOutputEvent
solid-category: test-support
solid-description: Carries a timestamped Codex tool response linked to its invocation, preserving native text and code-mode content blocks.
"""


class CodexToolOutputEvent(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)

    timestamp: datetime
    event_type: Literal["response_item"] = Field(validation_alias="type")
    payload_type: Literal["custom_tool_call_output", "function_call_output"] = Field(
        validation_alias=AliasPath("payload", "type"),
    )
    call_id: str = Field(validation_alias=AliasPath("payload", "call_id"))
    output: str | list[CodexOutputText] = Field(
        validation_alias=AliasPath("payload", "output"),
    )

    @property
    def texts(self) -> list[str]:
        if isinstance(self.output, str):
            return [self.output]
        return [block.text for block in self.output]
