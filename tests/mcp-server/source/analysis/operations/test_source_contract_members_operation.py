import pytest
from source.analysis.matching.source_requirement_matcher_factory import (
    SourceRequirementMatcherFactory,
)
from source.analysis.operations.source_contract_members_operation import (
    SourceContractMembersOperation,
)
from source.analysis.operations.source_declaration_members_input import (
    SourceDeclarationMembersInput,
)
from source.analysis.relationships.source_reference_candidate_resolver import (
    SourceReferenceCandidateResolver,
)
from source.analysis.relationships.source_relationship_resolver import (
    SourceRelationshipResolver,
)
from source.analyze_source_input import AnalyzeSourceInput
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.source_unit_identity import SourceUnitIdentity
from source.text_analysis_source import TextAnalysisSource

"""
solid-name: test_source_contract_members_operation
solid-category: integration-test
solid-spec: [SPEC-067]
solid-description: Verifies known requirement coverage, helper exclusion, fatal-call facts and unresolved contract evidence using shared source analysis and matching.
"""


@pytest.mark.parametrize(
    "source, members, limitations",
    [
        (
            'protocol Loading { func load() }\nclass Loader: Loading { func load() { parse() }; private func parse() { fatalError("unsupported") } }',
            ["load"],
            False,
        ),
        ("class Loader: Missing { func load() {} }", [], True),
        ("class Loader { func load() {} }", [], False),
        (
            "protocol Loading { func load() }\nclass Loader: Loading { func unrelated() {} }",
            [],
            True,
        ),
        ("protocol Loading {}\nclass Loader: Loading { func helper() {} }", [], False),
        (
            "protocol Loading { func load() }\nclass Loader { func load() {} }\nextension Loader: Loading {}",
            ["load"],
            False,
        ),
    ],
)
def test_contract_members_are_matched_not_guessed(source, members, limitations):
    analysis = (
        SourceAnalysisOperationFactory()
        .make()
        .execute(
            AnalyzeSourceInput(
                source=TextAnalysisSource(text=source, virtual_path="Loader.swift"),
            )
        )
    )
    owner = next(unit for unit in analysis.units if unit.name == "Loader")
    inventory = SourceRelationshipResolver(SourceReferenceCandidateResolver()).resolve(
        [analysis]
    )
    result = SourceContractMembersOperation(
        SourceRequirementMatcherFactory().make()
    ).execute(
        SourceDeclarationMembersInput(
            inventory=inventory,
            declaration=SourceUnitIdentity(
                source_identity=analysis.source_identity, unit_identity=owner.identity
            ),
        ),
    )

    assert [member.name for member in result.members] == members
    assert bool(result.limitations) is limitations
    assert [call.callee for call in result.calls] == [
        call.callee
        for call in analysis.calls
        if owner.start_offset <= call.start_offset
        and call.end_offset <= owner.end_offset
    ]
    for member in result.members:
        assert member.identity in result.context
        assert member.name in result.context
