"""Dispatches semantic evidence through injected ownership resolvers."""

from pathlib import Path

from source.analysis.provenance.source_declaration_ownership_resolver import (
    SourceSymbolOwnershipResolving,
)
from source.analysis.provenance.source_declaration_symbol import SourceDeclarationSymbol
from source.analysis.provenance.source_sdk_symbol import SourceSDKSymbol
from source.analysis.provenance.source_symbol_provenance import (
    SourceSymbolProvenance,
    SourceSymbolResolution,
)
from source.analysis.provenance.source_unresolved_symbol import SourceUnresolvedSymbol

"""
solid-name: SourceSymbolOwnershipResolver
solid-category: service
solid-spec: [SPEC-064]
solid-description: Delegates typed symbol evidence to declaration or locationless ownership resolution using a canonical project boundary.
"""


class SourceSymbolOwnershipResolver(
    SourceSymbolOwnershipResolving[SourceSymbolResolution]
):
    def __init__(
        self,
        declarations: SourceSymbolOwnershipResolving[SourceDeclarationSymbol],
        locationless: SourceSymbolOwnershipResolving[
            SourceSDKSymbol | SourceUnresolvedSymbol
        ],
    ) -> None:
        self._declarations = declarations
        self._locationless = locationless

    def resolve(
        self, resolution: SourceSymbolResolution, project_root: Path
    ) -> SourceSymbolProvenance:
        if not project_root.is_absolute():
            raise ValueError("Symbol ownership requires an absolute project root.")
        root = project_root.resolve()
        if resolution.kind == "declaration":
            return self._declarations.resolve(resolution, root)
        return self._locationless.resolve(resolution, root)
