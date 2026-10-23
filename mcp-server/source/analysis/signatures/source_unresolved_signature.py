"""Represents an explicitly unavailable structural signature."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: SourceUnresolvedSignature
solid-category: model
solid-spec: [SPEC-057]
solid-description: Retains the reason a declaration's signature cannot be extracted instead of presenting missing facts as a valid signature.
"""


class SourceUnresolvedSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["unresolved"] = "unresolved"
    reason: str = Field(
        default="Signature analysis is unavailable for this declaration", min_length=1
    )
