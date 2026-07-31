"""
solid-name: SessionValidationHandler
solid-category: service
solid-description: Validates whether a session is eligible for termination based on prerequisite conditions.
solid-tags: [hook]
"""

import os
import sys
from pathlib import Path
from typing import Callable, Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
for _d in (_MCP_DIR, _MCP_DIR / "session"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_decision import HookDecision  # noqa: E402
from hook_handling import HookHandling  # noqa: E402
from session_registry import validate_session_stop  # noqa: E402


class SessionStopApplicabilityChecking(Protocol):
    def applies(self, event: dict) -> bool: ...


class SessionStopValidating(Protocol):
    def validate(self, event: dict) -> HookDecision: ...


class SessionStopApplicabilityChecker(SessionStopApplicabilityChecking):
    """A session is eligible for validation once it has a session_id and isn't a re-entrant stop attempt."""

    def applies(self, event: dict) -> bool:
        if event.get("stop_hook_active"):
            return False
        return bool(event.get("session_id", ""))


class SessionStopValidator(SessionStopValidating):
    """Runs the required-tool-calls check and turns the result into a HookDecision."""

    def __init__(
        self,
        validate_fn: Callable = validate_session_stop,
        cwd_provider: Callable[[], str] = os.getcwd,
    ) -> None:
        self._validate = validate_fn
        self._cwd_provider = cwd_provider

    def validate(self, event: dict) -> HookDecision:
        transcript_path = event.get("transcript_path") or None
        cwd = event.get("cwd") or self._cwd_provider()
        result = self._validate(session_id=event["session_id"], transcript_path=transcript_path, cwd=cwd)
        if not result.get("allow", True):
            return HookDecision(allow=False, reason=result.get("reason", "Required MCP tools were not called."))
        return HookDecision(allow=True)


class SessionValidationHandler(HookHandling):
    """Coordination facade: filters via applicability, then delegates to the validator."""

    def __init__(
        self,
        applicability: SessionStopApplicabilityChecking = SessionStopApplicabilityChecker(),
        validator: SessionStopValidating = SessionStopValidator(),
    ) -> None:
        self._applicability = applicability
        self._validator = validator

    def should_handle(self, event: dict) -> bool:
        return self._applicability.applies(event)

    def handle(self, event: dict) -> HookDecision:
        return self._validator.validate(event)
