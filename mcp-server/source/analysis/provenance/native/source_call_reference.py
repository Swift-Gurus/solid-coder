"""Selects a call by exact source offset and independently resolved identity."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceCallReference
solid-category: model
solid-spec: [SPEC-064]
solid-description: Binds a return-contract query to the exact callee identity established in the reviewed source snapshot.
"""
class SourceCallReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    offset: int = Field(ge=0)
    symbol_id: str = Field(min_length=1)
