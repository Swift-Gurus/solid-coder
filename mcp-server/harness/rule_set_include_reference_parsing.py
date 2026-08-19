"""Defines recognition and parsing of all-rules include references."""

from __future__ import annotations

from typing import Protocol

from harness.rule_set_include_reference import RuleSetIncludeReference


"""
solid-name: RuleSetIncludeReferenceParsing
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for recognizing and decoding the explicit all-rules include reference.
"""
class RuleSetIncludeReferenceParsing(Protocol):
    def parse(self, raw: object) -> RuleSetIncludeReference | None: ...
