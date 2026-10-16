from typing import Protocol, TypeVar

from source.members.source_member_visibility import SourceMemberVisibility


Signature = TypeVar("Signature", contravariant=True)


"""
solid-name: SourceSignatureMatching
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for determining structural compatibility between required and candidate signature facts.
"""
class SourceSignatureMatching(Protocol[Signature]):
    def matches(self, requirement: Signature, implementation: Signature) -> bool: ...


"""
solid-name: SwiftModifierMatcher
solid-category: service
solid-spec: [SPEC-057]
solid-description: Compares behavioral member modifiers independently from declared visibility.
"""
class SwiftModifierMatcher(SourceSignatureMatching[list[str]]):
    def matches(self, requirement: list[str], implementation: list[str]) -> bool:
        visibility = {value.value for value in SourceMemberVisibility}
        return (
            [token for token in requirement if token not in visibility]
            == [token for token in implementation if token not in visibility]
        )
