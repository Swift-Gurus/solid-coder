from pydantic import BaseModel, ConfigDict, Field
from source.analysis.relationships.source_relationship_kind import (
    SourceRelationshipKind,
)
from source.analysis.signatures.source_type_reference import SourceTypeReference
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceDeclarationReference
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records an authored relationship reference with its declaring unit, source evidence, and unevaluated generic constraints.
"""


class SourceDeclarationReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    owner: SourceUnitIdentity
    kind: SourceRelationshipKind
    target: SourceTypeReference
    generic_parameters: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
