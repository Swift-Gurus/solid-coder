"""Defines a non-terminating gate that exposes its captured decision."""

from typing import Protocol

from gate_handling import GateHandling
from hook_decision import HookDecision


"""
solid-name: DecisionRevealingGate
solid-category: abstraction
solid-description: Contract for handling a review response and exposing its captured authorization decision.
solid-tags: [hook]
"""
class DecisionRevealingGate(GateHandling, Protocol):
    @property
    def decision(self) -> HookDecision: ...
