from pydantic import BaseModel, ConfigDict

from source.source_analysis import SourceAnalysis
from source.analysis.declarations.source_declaration_classification import SourceDeclarationClassification
from source.analysis.declarations.source_scoped_declaration import SourceScopedDeclaration


"""
solid-name: BindDeclarationClassificationsInput
solid-category: model
solid-spec: [SPEC-066]
solid-description: Associates a server-selected declaration inventory with complete model judgments before deterministic rule evaluation.
"""
class BindDeclarationClassificationsInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    analysis: SourceAnalysis
    declarations: list[SourceScopedDeclaration]
    classifications: list[SourceDeclarationClassification]
