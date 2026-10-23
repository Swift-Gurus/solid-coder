import pytest
from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from source.analysis.operations.bind_member_classifications_input import (
    BindMemberClassificationsInput,
)
from source.analysis.operations.bind_member_classifications_operation import (
    BindMemberClassificationsOperation,
)
from source.members.source_member import SourceMember
from source.members.source_member_classification import SourceMemberClassification
from source.members.source_member_kind import SourceMemberKind
from source.members.source_member_visibility import SourceMemberVisibility
from source.source_line_range import SourceLineRange
from validation.collection_identity_coverage_validator import (
    CollectionIdentityCoverageValidator,
)

"""
solid-name: test_bind_member_classifications_operation
solid-category: unit-test
solid-spec: [SPEC-067]
solid-description: Ensures member judgments cover the authoritative inventory exactly once and reuse the shared actionable replacement errors.
"""


@pytest.mark.parametrize(
    "submitted, error",
    [
        ([], "missing"),
        (["load"], "missing"),
        (["load", "load", "reset"], "duplicate"),
        (["load", "reset", "parse"], "unknown"),
        (["reset", "load"], None),
    ],
)
def test_member_classifications_require_complete_exact_coverage(submitted, error):
    members = [
        SourceMember(
            identity=name,
            name=name,
            kind=SourceMemberKind.METHOD,
            visibility=SourceMemberVisibility.INTERNAL,
            span=SourceLineRange(start=1, end=1),
        )
        for name in ["load", "reset"]
    ]
    request = BindMemberClassificationsInput(
        members=members,
        classifications=[
            SourceMemberClassification(
                member=name, classification="MEANINGFUL", evidence="Source body."
            )
            for name in submitted
        ],
    )
    operation = BindMemberClassificationsOperation(
        CollectionIdentityCoverageValidator(FlowValidationErrorFactory())
    )
    if error is not None:
        with pytest.raises(FlowValidationError, match=error) as rejection:
            operation.execute(request)
        assert "complete replacement" in str(rejection.value)
    else:
        result = operation.execute(request)
        assert [entry.member for entry in result.classifications] == ["load", "reset"]
