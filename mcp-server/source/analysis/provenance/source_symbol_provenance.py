"""Persists semantic evidence together with its repository ownership decision."""

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from source.analysis.provenance.source_declaration_symbol import SourceDeclarationSymbol
from source.analysis.provenance.source_sdk_symbol import SourceSDKSymbol
from source.analysis.provenance.source_symbol_ownership import SourceSymbolOwnership
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol

SourceSymbolResolution = Annotated[
    SourceDeclarationSymbol | SourceSDKSymbol | SourceUnresolvedSymbol,
    Field(discriminator="kind"),
]


"""
solid-name: SourceSymbolProvenance
solid-category: model
solid-spec: [SPEC-064]
solid-description: Preserves semantic resolution, canonical repository boundaries and auditable ownership decisions for replay.
"""
class SourceSymbolProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    resolution: SourceSymbolResolution
    project_root: Path
    ownership: SourceSymbolOwnership
    declaration_path: Path | None
    matched_exclusion: str | None = Field(default=None, min_length=1)
    reason: str = Field(min_length=1)
