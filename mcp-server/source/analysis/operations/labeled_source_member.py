from pydantic import Field

from source.analysis.matching.source_member_contribution import SourceMemberContribution


"""
solid-name: LabeledSourceMember
solid-category: model
solid-spec: [SPEC-057]
solid-description: Carries a source member contribution with an unambiguous cross-file presentation label for classification and submission accounting.
"""
class LabeledSourceMember(SourceMemberContribution):
    label: str = Field(min_length=1)
