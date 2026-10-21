from harness.operation_handling import OperationHandling
from source.analysis.operations.bind_member_classifications_input import BindMemberClassificationsInput
from validation.collection_identity_coverage_validator import CollectionIdentityCoverageValidating


"""
solid-name: BindMemberClassificationsOperation
solid-category: service
solid-spec: [SPEC-067]
solid-description: Reuses exact identity coverage validation and returns source-ordered member judgments without interpreting their categories or assigning severity.
"""
class BindMemberClassificationsOperation(OperationHandling[BindMemberClassificationsInput, BindMemberClassificationsInput]):
    def __init__(self, coverage: CollectionIdentityCoverageValidating) -> None:
        self._coverage = coverage

    def execute(self, operation_input: BindMemberClassificationsInput) -> BindMemberClassificationsInput:
        self._coverage.validate(
            expected_ids=[member.identity for member in operation_input.members],
            submitted_ids=[item.member for item in operation_input.classifications],
            identity_name="member (" + ", ".join(member.name for member in operation_input.members) + ")",
        )
        return BindMemberClassificationsInput(
            members=operation_input.members,
            classifications=[next(item for item in operation_input.classifications if item.member == member.identity)
                             for member in operation_input.members],
        )
