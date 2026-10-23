"""Decodes optional SourceKit symbol fields at the wire boundary."""

from pydantic import AliasPath, BaseModel, ConfigDict, Field, FileUrl
from source.analysis.provenance.semantic_position import SemanticPosition
from source.analysis.provenance.semantic_symbol_kind import SemanticSymbolKind

"""
solid-name: SourceKitSymbol
solid-category: model
solid-spec: [SPEC-064]
solid-description: Decodes semantic symbol identity, category, SDK evidence and declaration coordinates without manufacturing absent provider facts.
"""


class SourceKitSymbol(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)

    name: str | None = None
    symbol_id: str | None = Field(default=None, validation_alias="usr")
    kind: SemanticSymbolKind | None = None
    is_system: bool | None = Field(default=None, validation_alias="isSystem")
    declaration_uri: FileUrl | None = Field(
        default=None, validation_alias=AliasPath("bestLocalDeclaration", "uri")
    )
    declaration_position: SemanticPosition | None = Field(
        default=None,
        validation_alias=AliasPath("bestLocalDeclaration", "range", "start"),
    )
    module_name: str | None = Field(
        default=None, validation_alias=AliasPath("systemModule", "moduleName")
    )
