"""Carries one scoped inspection inventory into semantic resolution."""

from pydantic import BaseModel, ConfigDict, Field

from source.analysis.type_inspections.source_type_inspection import SourceTypeInspection
from source.repository_source_snapshot import RepositorySourceSnapshot


"""
solid-name: PreparedTypeInspections
solid-category: model
solid-spec: [SPEC-064]
solid-description: Carries an exact source snapshot, selected language, ordered inspections and inventory limitations.
"""
class PreparedTypeInspections(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot: RepositorySourceSnapshot
    language: str
    inspections: list[SourceTypeInspection] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
