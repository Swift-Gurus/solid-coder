"""Preserves SDK proof and unresolved outcomes without repository lookup."""

from pathlib import Path

from source.analysis.provenance.source_declaration_ownership_resolver import (
    SourceSymbolOwnershipResolving,
)
from source.analysis.provenance.source_sdk_symbol import SourceSDKSymbol
from source.analysis.provenance.source_symbol_ownership import SourceSymbolOwnership
from source.analysis.provenance.source_symbol_provenance import SourceSymbolProvenance
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol

"""
solid-name: SourceLocationlessOwnershipResolver
solid-category: service
solid-spec: [SPEC-064]
solid-description: Preserves verified SDK ownership and unknown semantic outcomes when declaration locations are unavailable.
"""


class SourceLocationlessOwnershipResolver(
    SourceSymbolOwnershipResolving[SourceSDKSymbol | SourceUnresolvedSymbol]
):
    def resolve(
        self, resolution: SourceSDKSymbol | SourceUnresolvedSymbol, project_root: Path
    ) -> SourceSymbolProvenance:
        match resolution.kind:
            case "sdk":
                ownership = SourceSymbolOwnership.EXTERNAL
                reason = resolution.evidence
            case "unresolved" | "ambiguous":
                ownership = SourceSymbolOwnership.UNKNOWN
                reason = resolution.reason
        return SourceSymbolProvenance(
            resolution=resolution,
            project_root=project_root,
            ownership=ownership,
            declaration_path=None,
            reason=reason,
        )
