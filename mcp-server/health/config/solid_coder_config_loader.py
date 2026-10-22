"""Loads typed configuration through substitutable configuration boundaries."""

from pathlib import Path
from typing import Protocol

from health.config.hc_config_core import read_llm_section, read_root_section, read_section
from config_section_reading import ConfigSectionReading
from config_values_reading import ConfigValuesReading
from harness.flow_validation_error import FlowValidationError
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.structured_model_decoding import StructuredModelDecoding
from solid_coder_config import SolidCoderConfig
from solid_coder_config_error import SolidCoderConfigError


"""
solid-name: SolidCoderConfigLoading
solid-category: abstraction
solid-spec: [SPEC-069]
solid-description: Contract for loading validated effective project configuration.
"""
class SolidCoderConfigLoading(Protocol):
    def load(self, cwd: Path | None = None) -> SolidCoderConfig: ...


"""
solid-name: SolidCoderConfigLoader
solid-category: boundary-adapter
solid-spec: [SPEC-069]
solid-description: Loads effective project configuration with hierarchical overrides, model-profile selection and field-level validation errors.
"""
class SolidCoderConfigLoader(SolidCoderConfigLoading):
    def __init__(
        self,
        root_reader: ConfigValuesReading | None = None,
        llm_reader: ConfigValuesReading | None = None,
        section_reader: ConfigSectionReading | None = None,
        decoder: StructuredModelDecoding[SolidCoderConfig] = PydanticModelDecoder(SolidCoderConfig),
    ) -> None:
        self._root_reader = read_root_section if root_reader is None else root_reader
        self._llm_reader = read_llm_section if llm_reader is None else llm_reader
        self._section_reader = read_section if section_reader is None else section_reader
        self._decoder = decoder

    def load(self, cwd: Path | None = None) -> SolidCoderConfig:
        raw = {
            **self._root_reader(_cwd=cwd),
            "llm": self._llm_reader(_cwd=cwd),
            "hooks": self._section_reader("hooks", _cwd=cwd),
            "inference": self._section_reader("inference", _cwd=cwd),
            "server": self._section_reader("server", _cwd=cwd),
            "flow_engine": self._section_reader("flow_engine", _cwd=cwd),
            "feature_flags": self._section_reader("feature_flags", _cwd=cwd),
            "frontmatter": self._section_reader("frontmatter", _cwd=cwd),
        }
        try:
            return self._decoder.decode(raw, "project configuration")
        except FlowValidationError as error:
            raise SolidCoderConfigError(str(error)) from error
