"""Validates the semantic server's selected position encoding."""

from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field

"""
solid-name: SourceKitInitialization
solid-category: model
solid-spec: [SPEC-064]
solid-description: Records the negotiated semantic position encoding.
"""


class SourceKitInitialization(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    position_encoding: Literal["utf-16"] = Field(
        default="utf-16",
        validation_alias=AliasPath("capabilities", "positionEncoding"),
    )
