from harness.operation_handling import OperationHandling
from source.analysis.matching.source_declaration_members import SourceDeclarationMembers
from source.analysis.matching.source_member_contribution import SourceMemberContribution
from source.analysis.matching.source_member_role import SourceMemberRole
from source.analysis.matching.source_owned_members_resolver import SourceOwnedMembersResolving
from source.analysis.matching.swift_modifier_matcher import SourceSignatureMatching
from source.analysis.operations.source_declaration_members_input import SourceDeclarationMembersInput
from source.analysis.relationships.source_relationship_kind import SourceRelationshipKind
from source.analysis.relationships.source_relationship_status import SourceRelationshipStatus
from source.members.source_member import SourceMember
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceDeclarationMembersOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Classifies inspected declaration and extension member contributions using bounded ownership and shared structural signatures without selecting visibility, assigning severity, or asserting semantic conformance.
"""
class SourceDeclarationMembersOperation(OperationHandling[SourceDeclarationMembersInput, SourceDeclarationMembers]):
    def __init__(
        self,
        members: SourceOwnedMembersResolving,
        signatures: SourceSignatureMatching[SourceMember],
    ) -> None:
        self._members = members
        self._signatures = signatures

    def execute(self, operation_input: SourceDeclarationMembersInput) -> SourceDeclarationMembers:
        inventory = operation_input.inventory
        declaration = operation_input.declaration
        owners = [
            unit for analysis in inventory.analyses for unit in analysis.units
            if SourceUnitIdentity(source_identity=analysis.source_identity, unit_identity=unit.identity) == declaration
        ]
        if len(owners) != 1:
            raise ValueError("Declaration member analysis requires one recorded declaration in the supplied inventory")
        declared = owners[0].members
        has_inheritance = any(
            link.reference.owner == declaration
            and link.reference.kind is SourceRelationshipKind.INHERITED_TYPE
            for link in inventory.relationships
        )
        contributions: list[SourceMemberContribution] = []
        for reference in self._members.resolve(inventory, owners=[declaration], extension_targets=[declaration]):
            matching = [member for member in declared if self._signatures.matches(member, reference.member)]
            uncertain_links = [link for link in reference.relationships if link.status is not SourceRelationshipStatus.CANDIDATE]
            if reference.owner == declaration:
                role = SourceMemberRole.DECLARED
                reason = "The member is directly declared by the selected source unit."
            elif uncertain_links:
                role = SourceMemberRole.UNRESOLVED
                reason = " ".join(link.reason for link in uncertain_links)
            elif matching:
                role = SourceMemberRole.IMPLEMENTATION
                reason = "The extension member matches a directly declared signature; semantic conformance is not verified."
            elif has_inheritance:
                role = SourceMemberRole.UNRESOLVED
                reason = "No direct signature matches; inherited member identity requires further resolution."
            elif not self._signatures.matches(reference.member, reference.member) or any(
                member.name == reference.member.name and member.kind == reference.member.kind
                and not self._signatures.matches(member, member)
                for member in declared
            ):
                role = SourceMemberRole.UNRESOLVED
                reason = "The available signatures do not support deciding whether this member implements an existing declaration."
            else:
                role = SourceMemberRole.ADDITIONAL
                reason = "The supported extension signature does not match any directly declared member."
            contributions.append(SourceMemberContribution(
                reference=reference, role=role, matching_declarations=matching, reason=reason,
            ))
        return SourceDeclarationMembers(inventory=inventory, declaration=declaration, members=contributions)
