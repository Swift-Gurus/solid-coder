"""Decodes one discovered metadata document through typed boundaries."""

from harness.flow_validation_error import FlowValidationError
from harness.structured_model_decoding import StructuredModelDecoding
from harness.yaml_support import YamlParsing
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.source_frontmatter import SourceFrontmatter

"""
solid-name: SourceFrontmatterDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-069]
solid-description: Converts source metadata documents into validated source facts.
"""


class SourceFrontmatterDecoder(SourceSyntaxParsing[str, SourceFrontmatter]):
    def __init__(
        self,
        yaml_parser: YamlParsing,
        model_decoder: StructuredModelDecoding[SourceFrontmatter],
    ) -> None:
        self._yaml_parser = yaml_parser
        self._model_decoder = model_decoder

    def parse(self, source: str) -> SourceFrontmatter:
        fields = [
            line.partition(":")[0]
            for line in source.splitlines()
            if line.startswith("solid-")
        ]
        if len(fields) != len(set(fields)):
            raise FlowValidationError(
                "Duplicate solid-frontmatter fields are not allowed"
            )
        return self._model_decoder.decode(
            self._yaml_parser.parse(source), "source frontmatter"
        )
