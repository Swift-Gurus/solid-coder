from pydantic import BaseModel, ConfigDict, Field

from source.analysis.relationships.source_related_declaration import SourceRelatedDeclaration
from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory
from source.source_unit_identity import SourceUnitIdentity
from source.source_search_output import SourceSearchOutput
from source.source_search_query import SourceSearchQuery
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: SourceDeclarationDiscovery
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves bounded declaration discovery, related source facts, and evidence limitations for reusable source workflows.
"""
class SourceDeclarationDiscovery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    inventory: SourceRelationshipInventory
    sources: list[TextAnalysisSource] = Field(default_factory=list)
    declaration: SourceUnitIdentity
    related_declarations: list[SourceRelatedDeclaration] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    queries: list[SourceSearchQuery] = Field(default_factory=list)
    searches: list[SourceSearchOutput] = Field(default_factory=list)
