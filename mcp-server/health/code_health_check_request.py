"""Defines one prospective code-health check request."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from patch_review_context import PatchReviewContext


"""
solid-name: CodeHealthCheckRequest
solid-category: model
solid-description: Represents prospective source content and its request-scoped review context for health validation.
solid-tags: [hook]
"""
class CodeHealthCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    content: str
    path: str = Field(min_length=1)
    language: str = Field(min_length=1)
    parent_session_id: str
    cwd: str = ""
    patch_context: Optional[PatchReviewContext] = None
    principle_names: list[str] = Field(default_factory=list)
