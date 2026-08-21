"""Defines the discriminated source-analysis operation input."""

from typing import Annotated, Union

from pydantic import BaseModel, ConfigDict, Field

from source.file_analysis_source import FileAnalysisSource
from source.text_analysis_source import TextAnalysisSource

AnalysisSource = Annotated[
    Union[FileAnalysisSource, TextAnalysisSource],
    Field(discriminator="kind"),
]


"""
solid-name: AnalyzeSourceInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Selects exactly one deterministic file-backed or text-backed analysis source.
"""
class AnalyzeSourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: AnalysisSource
