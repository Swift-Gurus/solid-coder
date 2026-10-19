"""Carries semantic evidence for an SDK-owned symbol."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceSDKSymbol
solid-category: model
solid-spec: [SPEC-064]
solid-description: Records a verified external SDK symbol without requiring locally available declaration source.
"""
class SourceSDKSymbol(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["sdk"] = "sdk"
    symbol_id: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
