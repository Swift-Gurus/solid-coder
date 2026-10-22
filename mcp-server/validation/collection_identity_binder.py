"""Binds completely accounted records in authoritative identity order."""

from typing import Generic, Protocol, TypeVar

from harness.flow_validation_error import FlowValidationError
from validation.collection_identity_coverage_validator import CollectionIdentityCoverageValidating


Record = TypeVar("Record")


"""
solid-name: CollectionIdentityBinding
solid-category: abstraction
solid-spec: [SPEC-069]
solid-description: Contract for validating complete record identity coverage and returning records in authoritative order.
"""
class CollectionIdentityBinding(Protocol, Generic[Record]):
    def bind(
        self, expected_ids: list[str], submitted_ids: list[str],
        records: list[Record], identity_name: str,
    ) -> list[Record]: ...


"""
solid-name: CollectionIdentityBinder
solid-category: service
solid-spec: [SPEC-069]
solid-description: Validates exactly-once identity accounting and orders corresponding typed records without interpreting their contents.
"""
class CollectionIdentityBinder(CollectionIdentityBinding[Record]):
    def __init__(self, coverage: CollectionIdentityCoverageValidating) -> None:
        self._coverage = coverage

    def bind(
        self, expected_ids: list[str], submitted_ids: list[str],
        records: list[Record], identity_name: str,
    ) -> list[Record]:
        if len(submitted_ids) != len(records):
            raise FlowValidationError(
                f"Each {identity_name} ID must identify exactly one record. "
                "Resubmit one complete replacement collection."
            )
        self._coverage.validate(expected_ids, submitted_ids, identity_name)
        return [records[submitted_ids.index(identity)] for identity in expected_ids]
