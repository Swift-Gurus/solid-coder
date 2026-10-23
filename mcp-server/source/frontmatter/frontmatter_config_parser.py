"""Reads project metadata vocabulary at the existing TOML boundary."""

from pathlib import Path

from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.structured_model_decoding import StructuredModelDecoding
from health.config.config_section_reading import ConfigSectionReading
from health.config.frontmatter_config import FrontmatterConfig
from health.config.hc_config_core import read_section
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing

_DEFAULT_DECODER: StructuredModelDecoding[FrontmatterConfig] = PydanticModelDecoder(
    FrontmatterConfig
)


"""
solid-name: FrontmatterConfigParser
solid-category: boundary-adapter
solid-spec: [SPEC-069]
solid-description: Loads and validates effective project additions to the registered metadata category vocabulary.
"""


class FrontmatterConfigParser(SourceSyntaxParsing[Path, FrontmatterConfig]):
    def __init__(
        self,
        section_reader: ConfigSectionReading = read_section,
        decoder: StructuredModelDecoding[FrontmatterConfig] = _DEFAULT_DECODER,
    ) -> None:
        self._section_reader = section_reader
        self._decoder = decoder

    def parse(self, source: Path) -> FrontmatterConfig:
        return self._decoder.decode(
            self._section_reader("frontmatter", _cwd=source),
            "frontmatter configuration",
        )
