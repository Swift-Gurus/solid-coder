from typing import Protocol

from source.analysis.matching.source_member_reference import SourceMemberReference
from source.analysis.matching.source_owned_members_resolver import SourceOwnedMembersResolving
from source.analysis.relationships.source_declaration_relationship import SourceDeclarationRelationship
from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory
from source.analysis.relationships.source_relationship_kind import SourceRelationshipKind


"""
solid-name: SourceRelatedMembersResolving
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for collecting candidate members through recorded declaration ownership and extension relationships.
"""
class SourceRelatedMembersResolving(Protocol):
    def resolve(
        self,
        inventory: SourceRelationshipInventory,
        relationship: SourceDeclarationRelationship,
    ) -> list[SourceMemberReference]: ...


"""
solid-name: SourceRelatedMembersResolver
solid-category: service
solid-spec: [SPEC-057]
solid-description: Collects directly related implementation members and extension defaults while retaining uncertain ownership evidence.
"""
class SourceRelatedMembersResolver(SourceRelatedMembersResolving):
    def __init__(self, members: SourceOwnedMembersResolving) -> None:
        self._members = members

    def resolve(
        self,
        inventory: SourceRelationshipInventory,
        relationship: SourceDeclarationRelationship,
    ) -> list[SourceMemberReference]:
        owner_links = [
            link for link in inventory.relationships
            if link.reference.kind is SourceRelationshipKind.EXTENSION_TARGET
            and link.reference.owner == relationship.reference.owner
        ]
        base_targets = {target for link in owner_links for target in link.candidates}
        members = self._members.resolve(
            inventory,
            owners=[relationship.reference.owner, *base_targets],
            extension_targets=[relationship.reference.owner, *base_targets, *relationship.candidates],
        )
        return [
            SourceMemberReference(
                owner=member.owner,
                member=member.member,
                relationships=[
                    *[link for link in owner_links if member.owner not in base_targets or member.owner in link.candidates],
                    *member.relationships,
                ],
            )
            for member in members
        ]
