"""Defines matching for one Swift parser-signal tag registration."""

from typing import Optional, Protocol

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
        parser_document: str,
        registration: SwiftSyntaxTagRegistration,
    ) -> Optional[str]: ...
