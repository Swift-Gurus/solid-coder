"""Matches typed Swift tag registrations against parser-document tokens."""

from typing import Optional

from source.source_tokens_resolving import SourceTokensResolving
from source.swift_syntax_registration_matching import SwiftSyntaxRegistrationMatching
from source.swift_syntax_tag_registration import SwiftSyntaxTagRegistration


"""
solid-name: SwiftSyntaxRegistrationMatcher
solid-category: service
solid-spec: [SPEC-039, SPEC-040]
solid-description: Selects an activating Swift syntax signal while respecting explicitly excluded signals.
"""
class SwiftSyntaxRegistrationMatcher(SwiftSyntaxRegistrationMatching):
    def __init__(self, token_resolver: SourceTokensResolving) -> None:
        self._token_resolver = token_resolver

    def match(
        self,
        parser_document: str,
        registration: SwiftSyntaxTagRegistration,
    ) -> Optional[str]:
        parser_tokens = self._token_resolver.resolve(parser_document)
        if any(
            signal.casefold() in parser_tokens
            for signal in registration.excluded_signals
        ):
            return None
        return next(
            (
                signal
                for signal in registration.signals
                if signal.casefold() in parser_tokens
            ),
            None,
        )
