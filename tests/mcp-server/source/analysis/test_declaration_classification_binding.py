import unittest

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from source.analysis.declarations.bind_declaration_classifications_input import (
    BindDeclarationClassificationsInput,
)
from source.analysis.declarations.bind_declaration_classifications_operation import (
    BindDeclarationClassificationsOperation,
)
from source.analysis.relationships.source_implementation_owners_resolver import (
    SourceImplementationOwnersResolver,
)
from source.analysis.relationships.source_reference_candidate_resolver import (
    SourceReferenceCandidateResolver,
)
from source.analysis.relationships.source_related_declarations_selector import (
    SourceRelatedDeclarationsSelector,
)
from source.analysis.relationships.source_relationship_resolver import (
    SourceRelationshipResolver,
)
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource
from validation.collection_identity_coverage_validator import (
    CollectionIdentityCoverageValidator,
)

"""
solid-name: TestDeclarationClassificationBinding
solid-category: integration-test
solid-spec: [SPEC-066]
solid-description: Verifies complete evidenced source classification binding and bounded conformance facts without trusting submitted counts or structural claims.
"""


class TestDeclarationClassificationBinding(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis = (
            SourceAnalysisOperationFactory()
            .make()
            .execute(
                AnalyzeSourceInput(
                    source=TextAnalysisSource(
                        virtual_path="Loader.swift",
                        text="""protocol Loading {}
protocol Caching {}
class Loader { let cache: any Caching }
extension Loader: Loading {}
""",
                    ),
                )
            )
        )
        self.entries = self.analysis.declarations[:3]
        self.operation = BindDeclarationClassificationsOperation(
            coverage=CollectionIdentityCoverageValidator(FlowValidationErrorFactory()),
            relationships=SourceRelationshipResolver(
                SourceReferenceCandidateResolver()
            ),
            owners=SourceImplementationOwnersResolver(
                SourceRelatedDeclarationsSelector()
            ),
        )
        self.records = [
            {
                "kind": "independent",
                "declaration_id": entry.identity,
                "has_business_logic": False,
                "additional_info": {
                    "reasoning": "A separate capability.",
                    "evidence": entry.unit.name,
                },
            }
            for entry in self.entries
        ]

    def bind(self, records):
        return self.operation.execute(
            BindDeclarationClassificationsInput.model_validate(
                {
                    "analysis": self.analysis,
                    "declarations": self.entries,
                    "classifications": records,
                }
            )
        )

    def test_exact_coverage_is_required_before_returning_bound_observations(
        self,
    ) -> None:
        for records, error in [
            (self.records[:-1], "missing"),
            ([*self.records, self.records[0]], "duplicate"),
            (
                [*self.records, {**self.records[0], "declaration_id": "invented"}],
                "unknown",
            ),
        ]:
            with (
                self.subTest(error=error),
                self.assertRaisesRegex(FlowValidationError, error),
            ):
                self.bind(records)
        result = self.bind(self.records)
        self.assertEqual(
            [entry.declaration.identity for entry in result.declarations],
            [entry.identity for entry in self.entries],
        )

    def test_extension_conformance_is_supported_but_consumption_is_not(self) -> None:
        records = [
            {
                "kind": "implemented_contract",
                "declaration_id": entry.identity,
                "related_declaration_id": self.entries[2].identity,
                "additional_info": {
                    "reasoning": "Same capability.",
                    "evidence": entry.unit.name,
                },
            }
            for entry in self.entries[:2]
        ]
        result = self.bind([*records, self.records[2]])

        self.assertTrue(result.declarations[0].declared_implementation)
        self.assertFalse(result.declarations[1].declared_implementation)
        self.assertTrue(result.declarations[0].has_declared_implementation)
        self.assertFalse(result.declarations[1].has_declared_implementation)

    def test_unknown_and_cyclic_associations_reject_complete_submission(self) -> None:
        record = {
            "kind": "cohesive_contract",
            "declaration_id": self.entries[0].identity,
            "related_declaration_id": "missing",
            "additional_info": {"reasoning": "Related.", "evidence": "Loading"},
        }
        with self.assertRaisesRegex(FlowValidationError, "related declaration"):
            self.bind([record, *self.records[1:]])

        first = {**record, "related_declaration_id": self.entries[1].identity}
        second = {
            **record,
            "declaration_id": self.entries[1].identity,
            "related_declaration_id": self.entries[0].identity,
        }
        with self.assertRaisesRegex(FlowValidationError, "independent"):
            self.bind([first, second, self.records[2]])

    def test_file_boundary_cannot_be_associated_with_a_callable_local_type(
        self,
    ) -> None:
        self.analysis = (
            SourceAnalysisOperationFactory()
            .make()
            .execute(
                AnalyzeSourceInput(
                    source=TextAnalysisSource(
                        virtual_path="Example.swift",
                        text="""func build() { struct Local {} }
private struct Helper {}
""",
                    ),
                )
            )
        )
        self.entries = [
            entry for entry in self.analysis.declarations if entry.unit.kind == "struct"
        ]
        records = [
            {
                "kind": "independent",
                "declaration_id": self.entries[0].identity,
                "has_business_logic": False,
                "additional_info": {
                    "reasoning": "Local data.",
                    "evidence": "struct Local",
                },
            },
            {
                "kind": "supporting_helper",
                "declaration_id": self.entries[1].identity,
                "related_declaration_id": self.entries[0].identity,
                "additional_info": {
                    "reasoning": "Claimed supporting role.",
                    "evidence": "struct Helper",
                },
            },
        ]
        with self.assertRaisesRegex(FlowValidationError, "related declaration"):
            self.bind(records)
