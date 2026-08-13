"""Defines a reusable-step overlay entry."""

from typing import Literal, Optional, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from harness.output_spec import OutputSpec


"""
solid-name: UsesWorkflowEntry
solid-category: model
solid-spec: [SPEC-030, SPEC-035]
solid-description: Represents a reusable step reference plus only the fields explicitly overridden by its declaring workflow.
"""
class UsesWorkflowEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    uses: str
    id: Optional[str] = None
    type: Optional[Literal["agent", "script", "command", "delegate"]] = None
    prompt: Optional[str] = None
    depends_on: Optional[list[str]] = None
    outputs: Optional[list[OutputSpec]] = None
    for_each: Optional[str] = None
    mode: Optional[Literal["subagent", "session"]] = None
    prompt_file: Optional[str] = None
    command: Optional[Union[str, list[str]]] = None
    script_file_reference: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("script_file_reference", "file"),
    )
    script_file: Optional[str] = None
    executor: Optional[str] = None
    args: Optional[list[str]] = None
    timeout_seconds: Optional[int] = None
    max_attempts: Optional[int] = None
