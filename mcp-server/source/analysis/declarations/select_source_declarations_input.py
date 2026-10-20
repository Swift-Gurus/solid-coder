from pydantic import BaseModel, ConfigDict, Field

from source.source_analysis import SourceAnalysis
from source.analysis.declarations.source_declaration_selection import SourceDeclarationSelection


"""
solid-name: SelectSourceDeclarationsInput
solid-category: model
solid-spec: [SPEC-066]
solid-description: Binds authoritative source analysis to authored structural declaration selectors.
"""
class SelectSourceDeclarationsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis: SourceAnalysis
    selections: list[SourceDeclarationSelection] = Field(min_length=1)
