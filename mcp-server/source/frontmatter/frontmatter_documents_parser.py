"""Discovers YAML metadata documents in source comment wrappers."""

from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

_UNIT_START = "solid-name:"
_SUPPORTED_FIELDS = (
    "solid-name:",
    "solid-description:",
    "solid-category:",
    "solid-tags:",
    "solid-stack:",
    "solid-spec:",
)
_COMMENT_WRAPPER_CHARACTERS = frozenset(" \t/#*<!-;")


"""
solid-name: FrontmatterDocumentsParser
solid-category: boundary-adapter
solid-spec: [SPEC-069]
solid-description: Discovers ordered source metadata documents while preserving comment boundaries and multiline descriptions.
"""
class FrontmatterDocumentsParser(SourceSyntaxParsing[str, list[str]]):
    def parse(self, content: str) -> list[str]:
        blocks: list[list[str]] = []
        current: list[str] = []
        indentation = 0
        in_block = False
        for line in content.splitlines():
            if line.lstrip().startswith("/*"):
                in_block = True
            if line.strip() in {'"""', "'''"}:
                in_block = not in_block
            normalized_line = line.casefold()
            field_indexes = [
                normalized_line.find(field)
                for field in _SUPPORTED_FIELDS
                if normalized_line.find(field) >= 0
                and all(
                    character in _COMMENT_WRAPPER_CHARACTERS
                    for character in normalized_line[
                        :normalized_line.find(field)
                    ]
                )
            ]
            if not field_indexes:
                normalized = line.rstrip()
                stripped = normalized.lstrip()
                if stripped in {"*/", "\"\"\"", "'''"}:
                    if stripped == "*/":
                        in_block = False
                    if current:
                        blocks.append(current)
                        current = []
                    continue
                wrapped = False
                for prefix in ("///", "//", "#", "*"):
                    if stripped.startswith(prefix):
                        wrapped = True
                        normalized = stripped.removeprefix(prefix).removeprefix(" ")
                        break
                if current and normalized[:1].isspace() and (in_block or wrapped):
                    relative_indentation = len(normalized) - len(normalized.lstrip()) - indentation
                    current.append(" " * max(2, relative_indentation) + normalized.lstrip())
                elif current and normalized:
                    blocks.append(current)
                    current = []
                continue
            field_index = min(field_indexes)
            yaml_line = line[field_index:].rstrip().removesuffix("*/").rstrip()
            if yaml_line.casefold().startswith(_UNIT_START) and current:
                blocks.append(current)
                current = []
            if not current:
                indentation = field_index if not line[:field_index].strip() else 0
            current.append(yaml_line)
        if current:
            blocks.append(current)
        return ["\n".join(block) for block in blocks]
