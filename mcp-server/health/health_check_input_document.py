"""Defines the persisted input for one isolated health-check run."""

from pydantic import BaseModel, ConfigDict, Field

from proposed_source_document import ProposedSourceDocument


"""
solid-name: HealthCheckInputDocument
solid-category: model
solid-description: Captures review identity, expected units, and proposed source changes for one health-check run.
solid-tags: [hook]
"""
class HealthCheckInputDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    file_path: str = Field(min_length=1)
    language: str = Field(min_length=1)
    output_dir: str = Field(min_length=1)
    expected_units: list[str]
    proposed_files: list[ProposedSourceDocument]
