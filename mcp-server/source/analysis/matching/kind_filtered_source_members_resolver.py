from findings.review_unit_kind import ReviewUnitKind
from source.analysis.matching.source_member_reference import SourceMemberReference
from source.analysis.matching.source_related_members_resolver import SourceRelatedMembersResolving
from source.analysis.relationships.source_declaration_relationship import SourceDeclarationRelationship
from source.analysis.relationships.source_relationship_inventory import SourceRelationshipInventory
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: KindFilteredSourceMembersResolver
solid-category: decorator
solid-spec: [SPEC-057]
solid-description: Applies configured declaration-kind exclusions to related member resolution so callers can distinguish implementation owners from declaration-only owners.
"""
class KindFilteredSourceMembersResolver(SourceRelatedMembersResolving):
    def __init__(
        self,
        members: SourceRelatedMembersResolving,
        excluded_kinds: set[ReviewUnitKind],
    ) -> None:
        self._members = members
        self._excluded_kinds = excluded_kinds

    def resolve(
        self,
        inventory: SourceRelationshipInventory,
        relationship: SourceDeclarationRelationship,
    ) -> list[SourceMemberReference]:
        owners = [
            SourceUnitIdentity(source_identity=analysis.source_identity, unit_identity=unit.identity)
            for analysis in inventory.analyses for unit in analysis.units
        ]
        if relationship.reference.owner not in owners:
            raise ValueError("The recorded relationship owner is absent from the supplied analyses")
        excluded = {
            SourceUnitIdentity(source_identity=analysis.source_identity, unit_identity=unit.identity)
            for analysis in inventory.analyses for unit in analysis.units
            if unit.kind in self._excluded_kinds
        }
        if relationship.reference.owner in excluded:
            return []
        return [
            member for member in self._members.resolve(inventory, relationship)
            if member.owner not in excluded
        ]
