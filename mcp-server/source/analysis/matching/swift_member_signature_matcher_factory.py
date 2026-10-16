from source.analysis.matching.swift_accessor_matcher import SwiftAccessorMatcher
from source.analysis.matching.swift_callable_signature_matcher import SwiftCallableSignatureMatcher
from source.analysis.matching.swift_member_signature_matcher import SwiftMemberSignatureMatcher
from source.analysis.matching.swift_modifier_matcher import SwiftModifierMatcher


"""
solid-name: SwiftMemberSignatureMatcherFactory
solid-category: factory
solid-spec: [SPEC-057]
solid-description: Composes structural member matching from shared callable, modifier, and accessor matching capabilities.
"""
class SwiftMemberSignatureMatcherFactory:
    def make(self) -> SwiftMemberSignatureMatcher:
        modifiers = SwiftModifierMatcher()
        return SwiftMemberSignatureMatcher(
            callables=SwiftCallableSignatureMatcher(modifiers=modifiers),
            modifiers=modifiers,
            accessors=SwiftAccessorMatcher(),
        )
