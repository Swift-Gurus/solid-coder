"""Defines a prospective path-backed review buffer."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict


"""
solid-name: BufferReviewTarget
solid-category: model
solid-spec: [SPEC-041]
solid-description: Carries exact prospective content and its project path without reading the current file.
"""
class BufferReviewTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["buffer"] = "buffer"
    path: Path
    content: str
