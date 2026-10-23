"""
solid-description: Contract that defines YAML text parsing into Python objects.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Any, Protocol

import yaml
from harness.flow_validation_error import FlowValidationError

"""
solid-name: YamlParsing
solid-category: abstraction
solid-description: Contract for parsing YAML text with shared validation errors.
"""


class YamlParsing(Protocol):
    """
    solid-description: Contract for parsing YAML-formatted text into Python objects.
    solid-category: abstraction
    """

    def parse(self, text: str) -> Any: ...


"""
solid-name: SafeYamlParser
solid-category: boundary-adapter
solid-spec: [SPEC-069]
solid-description: Parses YAML documents and reports malformed input through the shared validation contract.
"""


class SafeYamlParser:
    """
    solid-description: Parses YAML-formatted text into Python objects.
    solid-category: service
    """

    def parse(self, text: str) -> Any:
        try:
            result = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise FlowValidationError(f"Malformed YAML: {error}") from error
        return result if result is not None else {}
