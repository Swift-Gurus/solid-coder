"""Defines provision of the standard audited rule-step output."""

from typing import Protocol

from harness.output_spec import OutputSpec


"""
solid-name: RuleAdditionalInfoOutputProviding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for supplying the required reasoning-and-evidence output declared by review-rule steps.
"""
class RuleAdditionalInfoOutputProviding(Protocol):
    def provide(self) -> OutputSpec: ...
