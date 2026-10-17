from pydantic import BaseModel, ConfigDict, Field

from source.analysis.operations.source_declaration_discovery import SourceDeclarationDiscovery
from source.members.source_member_visibility import SourceMemberVisibility


"""
solid-name: SourceDeclarationContextInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Supplies bounded declaration discovery and explicit visibility exclusions for preparing shared definition and extension context.
"""
class SourceDeclarationContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    discovery: SourceDeclarationDiscovery
    excluded_visibilities: list[SourceMemberVisibility] = Field(default_factory=list)
