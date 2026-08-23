"""Defines one parser-signal registration for deterministic Swift tags."""

from dataclasses import dataclass, field


"""
solid-name: SwiftSyntaxTagRegistration
solid-category: model
solid-spec: [SPEC-039, SPEC-040]
solid-description: Associates exact Swift parser signals and exclusions with the file tags they activate.
"""
@dataclass(frozen=True)
class SwiftSyntaxTagRegistration:
    signals: list[str]
    tags: list[str]
    excluded_signals: list[str] = field(default_factory=list)
