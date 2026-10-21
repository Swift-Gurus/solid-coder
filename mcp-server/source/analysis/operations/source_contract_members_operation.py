from findings.review_unit_kind import ReviewUnitKind
from harness.operation_handling import OperationHandling
from source.analysis.matching.source_contract_members import SourceContractMembers
from source.analysis.matching.source_requirement_matcher import SourceRequirementsMatching
from source.analysis.operations.source_declaration_members_input import SourceDeclarationMembersInput
from source.analysis.relationships.source_relationship_kind import SourceRelationshipKind
from source.analysis.relationships.source_relationship_status import SourceRelationshipStatus
from source.members.source_member import SourceMember
from source.source_analysis_decision import SourceAnalysisDecision
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceContractMembersOperation
solid-category: service
solid-spec: [SPEC-067]
solid-description: Selects authoritative implementation candidates through existing requirement matching, retaining unknown contracts and scoped invocation evidence without assigning review severity.
"""
class SourceContractMembersOperation(OperationHandling[SourceDeclarationMembersInput, SourceContractMembers]):
    def __init__(self, requirements: SourceRequirementsMatching) -> None:
        self._requirements = requirements

    def execute(self, operation_input: SourceDeclarationMembersInput) -> SourceContractMembers:
        inventory = operation_input.inventory
        declaration = operation_input.declaration
        analyses = [item for item in inventory.analyses if item.source_identity == declaration.source_identity]
        owners = [unit for item in analyses for unit in item.units if unit.identity == declaration.unit_identity]
        if len(analyses) != 1 or len(owners) != 1:
            raise ValueError("Contract member analysis requires one recorded declaration in the supplied inventory")
        analysis = analyses[0]
        owner = owners[0]
        limitations = [item.message for item in analysis.diagnostics]
        if analysis.decision is not SourceAnalysisDecision.PARSED and not limitations:
            limitations.append("The language analysis cannot establish complete implementation coverage.")
        members: list[SourceMember] = []
        contract_owners = [declaration, *[
            link.reference.owner for link in inventory.relationships
            if link.reference.kind is SourceRelationshipKind.EXTENSION_TARGET
            and declaration in link.candidates
        ]]
        for link in inventory.relationships:
            if link.reference.owner not in contract_owners or link.reference.kind is not SourceRelationshipKind.INHERITED_TYPE:
                continue
            if link.status is not SourceRelationshipStatus.CANDIDATE:
                limitations.append(link.reason)
                continue
            contracts = [unit for item in inventory.analyses for unit in item.units
                if SourceUnitIdentity(source_identity=item.source_identity, unit_identity=unit.identity) in link.candidates
                and unit.kind is ReviewUnitKind.PROTOCOL]
            if not contracts:
                continue
            for contract in contracts:
                if contract.signature.kind == "declaration" and contract.signature.inherited_types:
                    limitations.append(f"Inherited requirements of {contract.name} require further resolution.")
            for match in self._requirements.match(inventory, link).matches:
                if match.status is not SourceRelationshipStatus.CANDIDATE:
                    limitations.append(f"{match.requirement.name}: {match.reason}")
                    continue
                for candidate in match.candidates:
                    if candidate.owner == declaration and candidate.member not in members:
                        members.append(candidate.member)
        members.sort(key=lambda member: owner.members.index(member))
        return SourceContractMembers(
            members=members,
            calls=[call for call in analysis.calls
                   if owner.start_offset <= call.start_offset and call.end_offset <= owner.end_offset],
            limitations=limitations,
            context="\n".join(
                f"Member: {member.name}; ID: {member.identity}; lines: {member.span.start}-{member.span.end}"
                for member in members
            ),
        )
