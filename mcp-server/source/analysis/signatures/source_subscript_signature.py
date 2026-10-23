"""Typed subscript header and accessor facts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from source.analysis.signatures.source_callable_signature import SourceCallableSignature

"""
solid-name: SourceSubscriptSignature
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records a subscript's callable header and declared accessor capabilities without inferring implementation behavior.
"""


class SourceSubscriptSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["subscript"] = "subscript"
    callable: SourceCallableSignature
    accessors: list[str] = Field(min_length=1)
