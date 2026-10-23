from harness.template_value_rendering import TemplateValueRendering
from source.analysis.declarations.source_scoped_declaration import (
    SourceScopedDeclaration,
)

"""
solid-name: SourceDeclarationInventoryRenderer
solid-category: utility
solid-spec: [SPEC-066]
solid-description: Renders compact declaration identities, lexical ownership, modifiers and locations without retransmitting source code or internal analysis objects.
"""


class SourceDeclarationInventoryRenderer(
    TemplateValueRendering[list[SourceScopedDeclaration]]
):
    def render(self, value: list[SourceScopedDeclaration]) -> str:
        return "\n".join(
            f"{entry.identity} | {entry.scope_kind.value} {entry.unit.kind.value} "
            f"{'.'.join([*(scope.name for scope in entry.scopes), entry.unit.name])} "
            f"| modifiers: {', '.join(entry.modifiers) or 'none'} "
            f"| lines {entry.unit.span.start}-{entry.unit.span.end}"
            for entry in value
        )
