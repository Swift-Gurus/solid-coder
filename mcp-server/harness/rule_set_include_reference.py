"""Defines the explicit all-rules include reference."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


"""
solid-name: RuleSetIncludeReference
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents the closed all-rules catalog inclusion reference.
"""
class RuleSetIncludeReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    rules: Literal["all"]
