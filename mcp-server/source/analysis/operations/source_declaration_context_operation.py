from findings.review_unit_kind import ReviewUnitKind
from harness.operation_handling import OperationHandling
from harness.template_value_rendering import TemplateValueRendering
from source.analysis.matching.source_declaration_members import SourceDeclarationMembers
from source.analysis.matching.source_member_role import SourceMemberRole
from source.analysis.operations.source_declaration_context import SourceDeclarationContext
from source.analysis.operations.source_declaration_context_input import SourceDeclarationContextInput
from source.analysis.operations.labeled_source_member import LabeledSourceMember
from source.analysis.operations.source_declaration_members_input import SourceDeclarationMembersInput
from source.analysis.relationships.source_relationship_kind import SourceRelationshipKind
from source.analysis.relationships.source_relationship_status import SourceRelationshipStatus
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceDeclarationContextOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Prepares definition and extension context through bounded ownership, shared member analysis, visibility selection, and source rendering while preserving unavailable evidence.
"""
class SourceDeclarationContextOperation(OperationHandling[SourceDeclarationContextInput, SourceDeclarationContext]):
    def __init__(
        self,
        members: OperationHandling[SourceDeclarationMembersInput, SourceDeclarationMembers],
        renderer: TemplateValueRendering[SourceDeclarationMembers],
    ) -> None:
        self._members = members
        self._renderer = renderer

    def execute(self, operation_input: SourceDeclarationContextInput) -> SourceDeclarationContext:
        discovery = operation_input.discovery
        links = [
            link for link in discovery.inventory.relationships
            if link.reference.owner == discovery.declaration
            and link.reference.kind is SourceRelationshipKind.EXTENSION_TARGET
        ]
        identities = [discovery.declaration]
        limitations = list(discovery.limitations)
        if links:
            identities = [identity for link in links
                          if link.status is SourceRelationshipStatus.CANDIDATE
                          for identity in link.candidates]
            limitations.extend(link.reason for link in links if link.status is not SourceRelationshipStatus.CANDIDATE)
        definitions = [
            unit for analysis in discovery.inventory.analyses for unit in analysis.units
            if SourceUnitIdentity(source_identity=analysis.source_identity, unit_identity=unit.identity) in identities
            and unit.kind is not ReviewUnitKind.EXTENSION
        ]
        if len(identities) != 1 or len(definitions) != 1:
            return SourceDeclarationContext(
                declaration=None, kind=None,
                limitations=[*limitations, "A unique definition could not be resolved from the inspected source evidence."],
            )
        declaration = identities[0]
        definition = definitions[0]
        inspected = self._members.execute(SourceDeclarationMembersInput(
            inventory=discovery.inventory, declaration=declaration,
        ))
        members = [
            LabeledSourceMember(
                reference=entry.reference,
                role=entry.role,
                matching_declarations=entry.matching_declarations,
                reason=entry.reason,
                label=f"{entry.reference.owner.source_identity}#{entry.reference.member.identity}",
            )
            for entry in inspected.members
            if entry.reference.member.visibility not in operation_input.excluded_visibilities
        ]
        limitations.extend(entry.reason for entry in members if entry.role is SourceMemberRole.UNRESOLVED)
        limitations.extend(
            f"Exact source is unavailable for member {entry.reference.member.identity}."
            for entry in members if not entry.reference.member.code
        )
        return SourceDeclarationContext(
            declaration=declaration, kind=definition.kind, name=definition.name,
            members=members, limitations=limitations,
            context=self._renderer.render(SourceDeclarationMembers(
                inventory=discovery.inventory, declaration=declaration, members=members,
            )),
        )
