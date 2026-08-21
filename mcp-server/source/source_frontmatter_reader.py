"""Reads comment-wrapped solid frontmatter through the YAML boundary."""

from harness.structured_model_decoding import StructuredModelDecoding
from harness.yaml_support import YamlParsing
from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_reading import SourceFrontmatterReading

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
solid-name: SourceFrontmatterReader
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Reads comment-wrapped solid YAML blocks and maps them directly into typed source frontmatter models.
"""
class SourceFrontmatterReader(SourceFrontmatterReading):
    def __init__(
        self,
        yaml_parser: YamlParsing,
        model_decoder: StructuredModelDecoding[SourceFrontmatter],
    ) -> None:
        self._yaml_parser = yaml_parser
        self._model_decoder = model_decoder

    def read(self, content: str) -> list[SourceFrontmatter]:
        blocks: list[list[str]] = []
        current: list[str] = []
        for line in content.splitlines():
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
                continue
            field_index = min(field_indexes)
            yaml_line = line[field_index:].strip()
            if yaml_line.casefold().startswith(_UNIT_START) and current:
                blocks.append(current)
                current = []
            current.append(yaml_line)
        if current:
            blocks.append(current)
        return [
            self._model_decoder.decode(
                self._yaml_parser.parse("\n".join(block)),
                "source frontmatter",
            )
            for block in blocks
        ]
