"""Applies canonical repository boundaries and exclusions to declarations."""

from pathlib import Path
from typing import Protocol, TypeVar

from gate.gate_exclusion_checker import ExclusionPatternResolving
from source.analysis.provenance.source_declaration_symbol import SourceDeclarationSymbol
from source.analysis.provenance.source_symbol_ownership import SourceSymbolOwnership
from source.analysis.provenance.source_symbol_provenance import SourceSymbolProvenance

SymbolEvidence = TypeVar("SymbolEvidence", contravariant=True)


"""
solid-name: SourceSymbolOwnershipResolving
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for resolving repository ownership from typed semantic evidence.
"""
class SourceSymbolOwnershipResolving(Protocol[SymbolEvidence]):
    def resolve(self, resolution: SymbolEvidence, project_root: Path) -> SourceSymbolProvenance: ...


"""
solid-name: SourceDeclarationOwnershipResolver
solid-category: service
solid-spec: [SPEC-064]
solid-description: Classifies declaration paths against canonical repository boundaries and configured exclusions without inferring dependency ownership from review eligibility.
"""
class SourceDeclarationOwnershipResolver(SourceSymbolOwnershipResolving[SourceDeclarationSymbol]):
    def __init__(self, exclusions: ExclusionPatternResolving) -> None:
        self._exclusions = exclusions

    def resolve(self, resolution: SourceDeclarationSymbol, project_root: Path) -> SourceSymbolProvenance:
        if not project_root.is_absolute():
            raise ValueError("Symbol ownership requires an absolute project root.")
        root = project_root.resolve()
        path = resolution.declaration_path.resolve()
        matched_exclusion = self._exclusions.matched_pattern(str(path)) if path.is_relative_to(root) else None
        if not path.is_relative_to(root):
            ownership = SourceSymbolOwnership.EXTERNAL
            reason = "The resolved declaration is outside the canonical repository boundary."
        elif matched_exclusion is not None:
            ownership = SourceSymbolOwnership.EXCLUDED
            reason = "The repository declaration is excluded from review; exclusion does not prove external ownership."
        else:
            ownership = SourceSymbolOwnership.DEVELOPER
            reason = "The resolved declaration is inside the repository and is not excluded."
        return SourceSymbolProvenance(
            resolution=resolution, project_root=root, ownership=ownership,
            declaration_path=path, matched_exclusion=matched_exclusion, reason=reason,
        )
