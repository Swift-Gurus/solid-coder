"""Defines the complete proposed source context for one apply-patch review."""

from pydantic import BaseModel, ConfigDict, Field

from patch_file_simulation import PatchFileSimulation


"""
solid-name: PatchReviewContext
solid-category: model
solid-description: Represents all proposed file changes belonging to one atomic review request.
solid-tags: [hook]
"""
class PatchReviewContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposed_files: list[PatchFileSimulation] = Field(min_length=1)
