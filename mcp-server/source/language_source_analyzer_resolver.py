"""Resolves deterministic source analyzers from typed registrations."""

from typing import Generic, TypeVar

from source.language_source_analyzer_registration import (
    LanguageSourceAnalyzerRegistration,
)
from source.language_source_analyzer_resolving import (
    LanguageSourceAnalyzerResolving,
)

AnalysisCapability = TypeVar("AnalysisCapability")


"""
solid-name: LanguageSourceAnalyzerResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves deterministic source analyzers through normalized typed registrations.
"""


class LanguageSourceAnalyzerResolver(
    LanguageSourceAnalyzerResolving[AnalysisCapability], Generic[AnalysisCapability]
):
    def __init__(
        self,
        registrations: list[LanguageSourceAnalyzerRegistration[AnalysisCapability]],
    ) -> None:
        self._registrations = registrations

    def resolve(self, language: str) -> AnalysisCapability | None:
        normalized = language.strip().lower()
        return next(
            (
                registration.analyzer
                for registration in self._registrations
                if registration.language == normalized
            ),
            None,
        )
