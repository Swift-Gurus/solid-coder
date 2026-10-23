from harness.collection_ratio_input import CollectionRatioInput
from harness.operation_handling import OperationHandling
from source.analysis.operations.validate_requirement_coverage_input import (
    ValidateRequirementCoverageInput,
)
from validation.collection_identity_coverage_validator import (
    CollectionIdentityCoverageValidating,
)

"""
solid-name: ValidateRequirementCoverageOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Validates complete requirement observations against authoritative matches before exposing them to collection reduction.
"""


class ValidateRequirementCoverageOperation(
    OperationHandling[ValidateRequirementCoverageInput, CollectionRatioInput]
):
    def __init__(
        self, coverage_validator: CollectionIdentityCoverageValidating
    ) -> None:
        self._coverage_validator = coverage_validator

    def execute(
        self, operation_input: ValidateRequirementCoverageInput
    ) -> CollectionRatioInput:
        available = operation_input.availability
        expected_ids = (
            [match.requirement.identity for match in operation_input.matches]
            if available.included and available.matches
            else []
        )
        self._coverage_validator.validate(
            expected_ids=expected_ids,
            submitted_ids=[
                entry.observation_id for entry in operation_input.coverage_entries
            ],
            identity_name="requirement",
        )
        self._coverage_validator.validate(
            expected_ids=expected_ids,
            submitted_ids=[
                entry.observation_id
                for entry in operation_input.coverage_entries
                if entry.included
            ],
            identity_name="included requirement",
        )
        return CollectionRatioInput(observations=operation_input.coverage_entries)
