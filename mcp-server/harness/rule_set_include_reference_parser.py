"""Recognizes and decodes the explicit all-rules include reference."""

from __future__ import annotations

from collections.abc import Mapping

from harness.rule_set_include_reference import RuleSetIncludeReference
from harness.rule_set_include_reference_parsing import (
    RuleSetIncludeReferenceParsing,
)
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: RuleSetIncludeReferenceParser
solid-category: boundary
solid-spec: [SPEC-039]
solid-description: Recognizes rule-set include data and decodes its closed all-rules form.
"""
class RuleSetIncludeReferenceParser(RuleSetIncludeReferenceParsing):
    def __init__(
        self,
        decoder: StructuredModelDecoding[RuleSetIncludeReference],
    ) -> None:
        self._decoder = decoder

    def parse(self, raw: object) -> RuleSetIncludeReference | None:
        if not isinstance(raw, Mapping) or "rules" not in raw:
            return None
        return self._decoder.decode(raw, "rule-set include reference")
