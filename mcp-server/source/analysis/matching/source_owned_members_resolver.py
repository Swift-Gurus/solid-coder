from typing import Protocol

from source.analysis.matching.source_member_reference import SourceMemberReference
from source.analysis.relationships.source_relationship_inventory import (
    SourceRelationshipInventory,
)
from source.analysis.relationships.source_relationship_kind import (
    SourceRelationshipKind,
)
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceOwnedMembersResolving
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for collecting members of supplied declaration owners and their recorded extension candidates without imposing review policy.
"""


class SourceOwnedMembersResolving(Protocol):
    def resolve(
        self,
        inventory: SourceRelationshipInventory,
        owners: list[SourceUnitIdentity],
        extension_targets: list[SourceUnitIdentity],
    ) -> list[SourceMemberReference]: ...


"""
solid-name: SourceOwnedMembersResolver
solid-category: service
solid-spec: [SPEC-057]
solid-description: Traverses inspected declarations once in source order to collect directly owned members and extension candidates while preserving relationship uncertainty.
"""


class SourceOwnedMembersResolver(SourceOwnedMembersResolving):
    def resolve(
        self,
        inventory: SourceRelationshipInventory,
        owners: list[SourceUnitIdentity],
        extension_targets: list[SourceUnitIdentity],
    ) -> list[SourceMemberReference]:
        members: list[SourceMemberReference] = []
        for analysis in inventory.analyses:
            for unit in analysis.units:
                identity = SourceUnitIdentity(
                    source_identity=analysis.source_identity,
                    unit_identity=unit.identity,
                )
                links = [
                    link
                    for link in inventory.relationships
                    if identity not in owners
                    and link.reference.kind is SourceRelationshipKind.EXTENSION_TARGET
                    and link.reference.owner == identity
                    and any(target in extension_targets for target in link.candidates)
                ]
                if identity in owners or links:
                    members.extend(
                        SourceMemberReference(
                            owner=identity, member=member, relationships=links
                        )
                        for member in unit.members
                    )
        return members
