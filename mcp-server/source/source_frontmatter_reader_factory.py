"""Composes typed source-frontmatter reading dependencies."""

from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.yaml_support import SafeYamlParser
from source.source_frontmatter import SourceFrontmatter
from source.source_frontmatter_reader import SourceFrontmatterReader


"""
solid-name: SourceFrontmatterReaderFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Creates readers for typed solid source frontmatter metadata.
"""
class SourceFrontmatterReaderFactory:
    def make(self) -> SourceFrontmatterReader:
        return SourceFrontmatterReader(
            yaml_parser=SafeYamlParser(),
            model_decoder=PydanticModelDecoder(
                model_type=SourceFrontmatter,
            ),
        )
