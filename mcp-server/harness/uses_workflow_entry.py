"""Defines a reusable-step overlay entry."""

from typing import Literal

from harness.output_spec import OutputSpec
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

"""
solid-name: UsesWorkflowEntry
solid-category: model
solid-spec: [SPEC-030, SPEC-035]
solid-description: Represents a reusable step reference plus only the fields explicitly overridden by its declaring workflow.
"""


class UsesWorkflowEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    uses: str
    id: str | None = None
    type: Literal["agent", "script", "command", "delegate"] | None = None
    prompt: str | None = None
    depends_on: list[str] | None = None
    outputs: list[OutputSpec] | None = None
    for_each: str | None = None
    mode: Literal["subagent", "session"] | None = None
    prompt_file: str | None = None
    command: str | list[str] | None = None
    script_file_reference: str | None = Field(
        default=None,
        validation_alias=AliasChoices("script_file_reference", "file"),
    )
    script_file: str | None = None
    executor: str | None = None
    args: list[str] | None = None
    timeout_seconds: int | None = None
    max_attempts: int | None = None
