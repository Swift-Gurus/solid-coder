"""Decodes the private native-worker request at its transport boundary."""

from pydantic import AliasPath, BaseModel, ConfigDict, Field


"""
solid-name: NativeSourceKitRequest
solid-category: model
solid-spec: [SPEC-064]
solid-description: Carries a correlated native semantic request without exposing transport dictionaries to worker logic.
"""
class NativeSourceKitRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    id: int
    payload: str = Field(validation_alias=AliasPath("params", "payload"), min_length=1)
