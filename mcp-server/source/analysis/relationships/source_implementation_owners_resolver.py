from typing import Protocol

from findings.review_unit_kind import ReviewUnitKind
from source.analysis.relationships.source_related_declarations_selector import SourceRelatedDeclarationsSelecting
from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory
from source.analysis.relationships.source_relationship_kind import SourceRelationshipKind
from source.analysis.relationships.source_relationship_status import SourceRelationshipStatus
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceImplementationOwnersResolving
solid-category: abstraction
solid-spec: [SPEC-066]
solid-description: Contract for finding bounded implementation owners through direct inheritance and extension declarations.
"""
class SourceImplementationOwnersResolving(Protocol):
    def resolve(self, inventory: SourceRelationshipInventory, declaration: SourceUnitIdentity) -> list[SourceUnitIdentity]: ...


"""
solid-name: SourceImplementationOwnersResolver
solid-category: service
solid-spec: [SPEC-066]
solid-description: Reuses related-declaration discovery to resolve direct or extension-declared implementation owners while excluding uncertain and protocol-only links.
"""
class SourceImplementationOwnersResolver(SourceImplementationOwnersResolving):
    def __init__(self, related: SourceRelatedDeclarationsSelecting) -> None:
        self._related = related

    def resolve(self, inventory: SourceRelationshipInventory, declaration: SourceUnitIdentity) -> list[SourceUnitIdentity]:
        owners: list[SourceUnitIdentity] = []
        for entry in self._related.select(inventory, declaration):
            if entry.relationship.status is not SourceRelationshipStatus.CANDIDATE:
                continue
            candidates = [entry.relationship.reference.owner]
            if entry.declaration.kind is ReviewUnitKind.EXTENSION:
                candidates = [
                    candidate for link in inventory.relationships
                    if link.reference.owner == entry.relationship.reference.owner
                    and link.reference.kind is SourceRelationshipKind.EXTENSION_TARGET
                    and link.status is SourceRelationshipStatus.CANDIDATE
                    for candidate in link.candidates
                ]
            owners.extend(
                candidate for candidate in candidates
                if candidate not in owners and any(
                    analysis.source_identity == candidate.source_identity
                    and unit.identity == candidate.unit_identity
                    and unit.kind not in {ReviewUnitKind.PROTOCOL, ReviewUnitKind.EXTENSION}
                    for analysis in inventory.analyses for unit in analysis.units
                )
            )
        return owners
