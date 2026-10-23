from typing import Protocol

from findings.review_unit_kind import ReviewUnitKind
from source.analysis.matching.source_related_members_resolver import (
    SourceRelatedMembersResolving,
)
from source.analysis.matching.source_requirement_match import SourceRequirementMatch
from source.analysis.matching.source_requirement_matches import SourceRequirementMatches
from source.analysis.matching.swift_modifier_matcher import SourceSignatureMatching
from source.analysis.relationships.source_declaration_relationship import (
    SourceDeclarationRelationship,
)
from source.analysis.relationships.source_relationship_inventory import (
    SourceRelationshipInventory,
)
from source.analysis.relationships.source_relationship_kind import (
    SourceRelationshipKind,
)
from source.analysis.relationships.source_relationship_status import (
    SourceRelationshipStatus,
)
from source.members.source_member import SourceMember
from source.source_unit_identity import SourceUnitIdentity

"""
solid-name: SourceRequirementsMatching
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for matching direct interface requirements to related implementation candidates while preserving source evidence and uncertainty.
"""


class SourceRequirementsMatching(Protocol):
    def match(
        self,
        inventory: SourceRelationshipInventory,
        relationship: SourceDeclarationRelationship,
    ) -> SourceRequirementMatches: ...


"""
solid-name: SourceRequirementMatcher
solid-category: service
solid-spec: [SPEC-057]
solid-description: Resolves bounded implementation candidates for direct protocol requirements without claiming verified conformance or repository completeness.
"""


class SourceRequirementMatcher(SourceRequirementsMatching):
    def __init__(
        self,
        members: SourceRelatedMembersResolving,
        signatures: SourceSignatureMatching[SourceMember],
    ) -> None:
        self._members = members
        self._signatures = signatures

    def match(
        self,
        inventory: SourceRelationshipInventory,
        relationship: SourceDeclarationRelationship,
    ) -> SourceRequirementMatches:
        if relationship not in inventory.relationships:
            raise ValueError(
                "Requirement matching requires a relationship recorded in the supplied inventory"
            )
        if relationship.reference.kind is not SourceRelationshipKind.INHERITED_TYPE:
            raise ValueError(
                "Requirement matching requires an inherited-type relationship"
            )
        members = self._members.resolve(inventory, relationship)
        matches: list[SourceRequirementMatch] = []
        for analysis in inventory.analyses:
            for unit in analysis.units:
                interface = SourceUnitIdentity(
                    source_identity=analysis.source_identity,
                    unit_identity=unit.identity,
                )
                if (
                    interface not in relationship.candidates
                    or unit.kind is not ReviewUnitKind.PROTOCOL
                ):
                    continue
                for requirement in unit.members:
                    candidates = [
                        member
                        for member in members
                        if self._signatures.matches(requirement, member.member)
                    ]
                    links = [
                        link
                        for candidate in candidates
                        for link in candidate.relationships
                    ]
                    if not candidates:
                        status = SourceRelationshipStatus.UNRESOLVED
                        reason = "No supported signature candidate was found; implementation absence or nonconformance is not established."
                    elif relationship.status is not SourceRelationshipStatus.CANDIDATE:
                        status = relationship.status
                        reason = relationship.reason
                    elif any(
                        link.status is SourceRelationshipStatus.AMBIGUOUS
                        for link in links
                    ):
                        status = SourceRelationshipStatus.AMBIGUOUS
                        reason = (
                            "A matching member has ambiguous declaration ownership."
                        )
                    elif any(
                        link.status is SourceRelationshipStatus.UNRESOLVED
                        for link in links
                    ):
                        status = SourceRelationshipStatus.UNRESOLVED
                        reason = "A matching member requires unresolved declaration or conditional-applicability analysis."
                    elif len(candidates) > 1:
                        status = SourceRelationshipStatus.AMBIGUOUS
                        reason = "Multiple related members match the signature; implementation dispatch is not resolved."
                    else:
                        status = SourceRelationshipStatus.CANDIDATE
                        reason = "One related member matches the supported signature shape; semantic conformance is not verified."
                    matches.append(
                        SourceRequirementMatch(
                            interface=interface,
                            requirement=requirement,
                            status=status,
                            candidates=candidates,
                            reason=reason,
                        )
                    )
        return SourceRequirementMatches(
            inventory=inventory, relationship=relationship, matches=matches
        )
