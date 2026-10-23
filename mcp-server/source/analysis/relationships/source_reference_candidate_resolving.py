from typing import Protocol

from source.analysis.relationships.source_declaration_reference import (
    SourceDeclarationReference,
)
from source.analysis.relationships.source_declaration_relationship import (
    SourceDeclarationRelationship,
)
from source.source_analysis import SourceAnalysis

"""
solid-name: SourceReferenceCandidateResolving
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for identifying bounded declaration candidates and preserving unresolved or ambiguous source references.
"""


class SourceReferenceCandidateResolving(Protocol):
    def resolve(
        self,
        reference: SourceDeclarationReference,
        analyses: list[SourceAnalysis],
    ) -> SourceDeclarationRelationship: ...
