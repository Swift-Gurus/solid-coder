"""Defines one proposed source document available to an MCP-owned review."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: ProposedSourceDocument
solid-category: model
solid-description: Represents one path-identified source revision available before its write is authorized.
solid-tags: [hook]
"""
class ProposedSourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    file_path: str = Field(min_length=1)
    content: str
