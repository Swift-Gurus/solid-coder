"""Composes typed source-frontmatter reading dependencies."""

from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.yaml_support import SafeYamlParser
from source.frontmatter.frontmatter_documents_parser import FrontmatterDocumentsParser
from source.frontmatter.source_frontmatter_decoder import SourceFrontmatterDecoder
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
            documents=FrontmatterDocumentsParser(),
            decoder=SourceFrontmatterDecoder(
                yaml_parser=SafeYamlParser(),
                model_decoder=PydanticModelDecoder(model_type=SourceFrontmatter),
            ),
        )
