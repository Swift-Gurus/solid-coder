from pydantic import BaseModel, ConfigDict

from source.analysis.relationships.source_declaration_relationship import SourceDeclarationRelationship
from source.source_unit import SourceUnit


"""
solid-name: SourceRelatedDeclaration
solid-category: model
solid-spec: [SPEC-057]
solid-description: Retains a related declaration's readable identity and structural facts alongside its bounded relationship evidence.
"""
class SourceRelatedDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration: SourceUnit
    relationship: SourceDeclarationRelationship
