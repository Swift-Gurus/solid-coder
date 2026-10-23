from pydantic import BaseModel, ConfigDict, Field
from source.analysis.declarations.source_scoped_declaration import (
    SourceScopedDeclaration,
)

"""
solid-name: SourceDeclarationSelectionResult
solid-category: model
solid-spec: [SPEC-066]
solid-description: Preserves selected source declarations, compact model-facing metadata and analysis limitations for auditable classification.
"""


class SourceDeclarationSelectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declarations: list[SourceScopedDeclaration] = Field(default_factory=list)
    context: str = ""
    limitations: list[str] = Field(default_factory=list)
