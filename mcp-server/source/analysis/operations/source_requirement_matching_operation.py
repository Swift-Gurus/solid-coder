from harness.operation_handling import OperationHandling
from source.analysis.matching.source_requirement_matcher import (
    SourceRequirementsMatching,
)
from source.analysis.matching.source_requirement_matches import SourceRequirementMatches
from source.analysis.operations.match_source_requirements_input import (
    MatchSourceRequirementsInput,
)

"""
solid-name: SourceRequirementMatchingOperation
solid-category: adapter
solid-spec: [SPEC-057]
solid-description: Exposes requirement implementation candidates and retained uncertainty as a typed engine-owned operation without classifying behavior or calculating scores.
"""


class SourceRequirementMatchingOperation(
    OperationHandling[MatchSourceRequirementsInput, SourceRequirementMatches]
):
    def __init__(self, matcher: SourceRequirementsMatching) -> None:
        self._matcher = matcher

    def execute(
        self, operation_input: MatchSourceRequirementsInput
    ) -> SourceRequirementMatches:
        return self._matcher.match(
            operation_input.inventory, operation_input.relationship
        )
