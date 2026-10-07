"""Defines matching for one Swift parser-signal tag registration."""

from typing import Protocol

from source.source_evidence import SourceEvidence
from source.swift_syntax_tag_registration import SwiftSyntaxTagRegistration


"""
solid-name: SwiftSyntaxRegistrationMatching
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-040]
solid-description: Contract for selecting the source signal that activates one Swift technology-tag registration.
"""
class SwiftSyntaxRegistrationMatching(Protocol):
    def match(
        self,
        signals: list[SourceEvidence],
        registration: SwiftSyntaxTagRegistration,
    ) -> SourceEvidence | None: ...


"""
solid-name: SwiftSyntaxRegistrationMatcher
solid-category: service
solid-spec: [SPEC-039, SPEC-040, SPEC-057]
solid-description: Selects an activating Swift syntax signal while respecting explicitly excluded signals.
"""
class SwiftSyntaxRegistrationMatcher(SwiftSyntaxRegistrationMatching):
    def match(
        self, signals: list[SourceEvidence], registration: SwiftSyntaxTagRegistration,
    ) -> SourceEvidence | None:
        available = {signal.fact.casefold() for signal in signals}
        if any(signal.casefold() in available for signal in registration.excluded_signals):
            return None
        return next(
            (
                evidence for signal in registration.signals for evidence in signals
                if evidence.fact.casefold() == signal.casefold()
            ),
            None,
        )
