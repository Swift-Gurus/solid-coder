"""Defines one unvalidated workflow-step declaration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, ClassVar, Optional, Union

from pydantic import AliasChoices, ConfigDict, Field

from harness.output_spec import OutputSpec


"""
solid-name: StepDeclaration
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Represents an unvalidated workflow step for later validation.
"""
@dataclass(frozen=True)
class StepDeclaration:
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: Optional[str] = None
    type: str = "agent"
    prompt: Optional[str] = None
    depends_on: Optional[list[str]] = None
    outputs: list[OutputSpec] = field(default_factory=list)
    for_each: Optional[str] = None
    mode: Optional[str] = None
    prompt_file: Optional[str] = None
    command: Optional[Union[str, list[str]]] = None
    script_file_reference: Annotated[
        Optional[str],
        Field(validation_alias=AliasChoices("script_file_reference", "file")),
    ] = None
    script_file: Optional[str] = None
    executor: Optional[str] = None
    args: Optional[list[str]] = None
    timeout_seconds: Optional[int] = None
    max_attempts: int = 3
    source_file: Optional[str] = None
