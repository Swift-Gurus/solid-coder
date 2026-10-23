from pydantic import BaseModel, ConfigDict
from source.source_analysis import SourceAnalysis

"""
solid-name: ResolveSourceRelationshipsInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Carries inspected source snapshots for bounded declaration relationship analysis without requesting repository discovery.
"""


class ResolveSourceRelationshipsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analyses: list[SourceAnalysis]
