"""Defines serialization of generated rule-set members."""

from typing import Protocol

from harness.rule_set_member_include import RuleSetMemberInclude


"""
solid-name: RuleSetMemberSerializing
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for adapting a typed rule-set member to the raw include traversal boundary.
"""
class RuleSetMemberSerializing(Protocol):
    def serialize(self, member: RuleSetMemberInclude) -> dict[str, object]: ...
