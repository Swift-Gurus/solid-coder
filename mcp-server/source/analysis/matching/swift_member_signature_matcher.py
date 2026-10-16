from source.analysis.matching.swift_modifier_matcher import SourceSignatureMatching
from source.analysis.signatures.source_callable_signature import SourceCallableSignature
from source.members.source_member import SourceMember


"""
solid-name: SwiftMemberSignatureMatcher
solid-category: boundary-adapter
solid-spec: [SPEC-057]
solid-description: Determines structural compatibility between supported Swift member requirements and implementation candidates.
"""
class SwiftMemberSignatureMatcher(SourceSignatureMatching[SourceMember]):
    def __init__(
        self,
        callables: SourceSignatureMatching[SourceCallableSignature],
        modifiers: SourceSignatureMatching[list[str]],
        accessors: SourceSignatureMatching[list[str]],
    ) -> None:
        self._callables = callables
        self._modifiers = modifiers
        self._accessors = accessors

    def matches(self, requirement: SourceMember, implementation: SourceMember) -> bool:
        if requirement.kind != implementation.kind or requirement.name != implementation.name:
            return False
        expected = requirement.signature
        actual = implementation.signature
        if expected.kind != actual.kind:
            return False
        match expected.kind:
            case "callable":
                return self._callables.matches(expected, actual)
            case "value":
                return (
                    expected.value_type == actual.value_type
                    and self._modifiers.matches(expected.modifiers, actual.modifiers)
                    and self._accessors.matches(expected.accessors, actual.accessors)
                )
            case "subscript":
                return (
                    self._callables.matches(expected.callable, actual.callable)
                    and self._accessors.matches(expected.accessors, actual.accessors)
                )
            case _:
                return False
