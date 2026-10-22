"""Carries an output location returned by a pipeline tool."""

from pydantic import BaseModel, ConfigDict


"""
solid-name: PipelineOutputRoot
solid-category: model
solid-description: Identifies the pipeline output location recorded in a tool result.
"""
class PipelineOutputRoot(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    output_root: str = ""
