from source.analysis.matching.swift_modifier_matcher import SourceSignatureMatching

"""
solid-name: SwiftAccessorMatcher
solid-category: service
solid-spec: [SPEC-057]
solid-description: Determines whether a candidate property's accessor capabilities match its required accessors and effects.
"""


class SwiftAccessorMatcher(SourceSignatureMatching[list[str]]):
    def matches(self, requirement: list[str], implementation: list[str]) -> bool:
        retained = (
            implementation
            if "set" in requirement
            else [token for token in implementation if token != "set"]
        )
        return requirement == retained
