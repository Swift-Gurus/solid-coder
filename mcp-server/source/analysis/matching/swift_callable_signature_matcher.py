from source.analysis.matching.swift_modifier_matcher import SourceSignatureMatching
from source.analysis.signatures.source_callable_signature import SourceCallableSignature

"""
solid-name: SwiftCallableSignatureMatcher
solid-category: service
solid-spec: [SPEC-057]
solid-description: Determines structural compatibility between callable requirements and candidate implementations without resolving generic substitutions.
"""


class SwiftCallableSignatureMatcher(SourceSignatureMatching[SourceCallableSignature]):
    def __init__(self, modifiers: SourceSignatureMatching[list[str]]) -> None:
        self._modifiers = modifiers

    def matches(
        self,
        requirement: SourceCallableSignature,
        implementation: SourceCallableSignature,
    ) -> bool:
        return (
            not requirement.generic_parameters
            and not implementation.generic_parameters
            and not requirement.constraints
            and not implementation.constraints
            and requirement.parameters == implementation.parameters
            and requirement.return_type == implementation.return_type
            and self._modifiers.matches(requirement.modifiers, implementation.modifiers)
        )
