"""
solid-description: Contract for components that need to log, allow, or block operations.
solid-category: abstraction
"""

from typing import Protocol

from logging_protocol import Logging
from hook_responding import HookResponding


class GateHandling(Logging, HookResponding, Protocol):
    """Narrow gate protocol for components that need to log, allow, or block.

    Kept distinct from its sole production conformer (HookGate) so gate/
    consumers (GateOrchestrator, WriteGateCoordinator, SafeHealthChecker, ...)
    and their tests can depend on and inject any duck-typed gate — including
    test fakes — without coupling to the concrete HookGate facade.
    """
