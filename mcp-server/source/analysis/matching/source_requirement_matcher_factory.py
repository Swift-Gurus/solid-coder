from findings.review_unit_kind import ReviewUnitKind
from source.analysis.matching.kind_filtered_source_members_resolver import (
    KindFilteredSourceMembersResolver,
)
from source.analysis.matching.source_owned_members_resolver import (
    SourceOwnedMembersResolver,
)
from source.analysis.matching.source_related_members_resolver import (
    SourceRelatedMembersResolver,
)
from source.analysis.matching.source_requirement_matcher import SourceRequirementMatcher
from source.analysis.matching.swift_member_signature_matcher_factory import (
    SwiftMemberSignatureMatcherFactory,
)

"""
solid-name: SourceRequirementMatcherFactory
solid-category: factory
solid-spec: [SPEC-057]
solid-description: Provides bounded direct-protocol requirement matching with explicit ownership uncertainty.
"""


class SourceRequirementMatcherFactory:
    def make(self) -> SourceRequirementMatcher:
        return SourceRequirementMatcher(
            members=KindFilteredSourceMembersResolver(
                members=SourceRelatedMembersResolver(
                    members=SourceOwnedMembersResolver()
                ),
                excluded_kinds={
                    ReviewUnitKind.PROTOCOL,
                    ReviewUnitKind.FUNCTION,
                    ReviewUnitKind.DOCUMENT,
                },
            ),
            signatures=SwiftMemberSignatureMatcherFactory().make(),
        )
