"""Exercises exact identity binding independently of any workflow payload."""

import unittest

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from validation.collection_identity_binder import CollectionIdentityBinder
from validation.collection_identity_coverage_validator import CollectionIdentityCoverageValidator


"""
solid-name: TestCollectionIdentityBinder
solid-category: unit-test
solid-spec: [SPEC-069]
solid-description: Verifies typed records retain authoritative ordering and reject incomplete or inconsistent identity accounting.
"""
class TestCollectionIdentityBinder(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = CollectionIdentityBinder(
            CollectionIdentityCoverageValidator(FlowValidationErrorFactory()),
        )

    def test_records_are_returned_in_expected_order(self) -> None:
        self.assertEqual(
            self.sut.bind(["first", "second"], ["second", "first"], [20, 10], "record"),
            [10, 20],
        )

    def test_empty_collection_remains_empty(self) -> None:
        self.assertEqual(self.sut.bind([], [], [], "record"), [])

    def test_missing_duplicate_unknown_and_misaligned_records_are_rejected(self) -> None:
        for identities, records in [([], []), (["first", "first"], [1, 2]), (["other"], [1]), (["first"], [])]:
            with self.subTest(identities=identities, records=records):
                with self.assertRaisesRegex(FlowValidationError, "complete replacement"):
                    self.sut.bind(["first"], identities, records, "record")
