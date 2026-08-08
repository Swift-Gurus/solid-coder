"""Defines construction of non-terminating decision gates."""

from typing import Protocol

from decision_revealing_gate import DecisionRevealingGate
from logging_protocol import Logging


"""
solid-name: DecisionGateCreating
solid-category: abstraction
solid-description: Contract for constructing a decision-capturing gate backed by diagnostic logging.
solid-tags: [hook]
"""
class DecisionGateCreating(Protocol):
    def create(self, logger: Logging) -> DecisionRevealingGate: ...
