from harness.template_value_rendering import TemplateValueRendering
from source.analysis.matching.source_declaration_members import SourceDeclarationMembers
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceDeclarationContextRenderer
solid-category: utility
solid-spec: [SPEC-057]
solid-description: Renders a selected definition header and eligible member source excerpts with stable identities and provenance, without exposing unrelated inventory content.
"""
class SourceDeclarationContextRenderer(TemplateValueRendering[SourceDeclarationMembers]):
    def render(self, value: SourceDeclarationMembers) -> str:
        definition = next(
            unit for analysis in value.inventory.analyses for unit in analysis.units
            if SourceUnitIdentity(source_identity=analysis.source_identity, unit_identity=unit.identity) == value.declaration
        )
        sections = [f"Definition: {definition.kind.value} {definition.name}"]
        signature = definition.signature
        if signature.kind == "declaration":
            sections.append("Modifiers: " + " ".join(signature.modifiers))
            sections.append("Inherited declarations: " + ", ".join(
                " ".join(reference.tokens) for reference in signature.inherited_types
            ))
        for contribution in value.members:
            member = contribution.reference.member
            sections.append(
                f"Member: {member.identity}\n"
                f"Source: {contribution.reference.owner.source_identity}:{member.span.start}-{member.span.end}\n"
                f"Role: {contribution.role.value}\n{member.code}"
            )
        return "\n\n".join(sections)
