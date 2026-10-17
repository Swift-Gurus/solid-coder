"""
solid-description: Safely validates content and indicates whether validation succeeded.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from gate_protocols import GateHandling, HealthChecking
from health_check_outcome import HealthCheckOutcome
from health_outcome_renderer import HealthOutcomeRendering


"""
solid-name: SafeHealthChecker
solid-category: service
solid-description: Safely authorizes prospective content from health outcomes, preserving review warnings and failing closed on checker errors.
solid-tags: [hook]
"""
class SafeHealthChecker:
    """Invokes the health checker, handles errors, and returns True if the content is clean."""

    def __init__(self, checker: HealthChecking[HealthCheckOutcome], renderer: HealthOutcomeRendering) -> None:
        self._checker = checker
        self._renderer = renderer

    def check(self, content: str, path: str, language: str, session_id: str, gate: GateHandling, file_name: str, cwd: str = "") -> bool:
        try:
            outcome = self._checker.check(content, path, language, session_id, cwd)
            decision = self._renderer.render(outcome)
        except Exception as exc:
            gate.log(f"BLOCK {file_name}: health subprocess error: {exc}")
            gate.block(
                f"[health-check] Gate subprocess failed — the write is blocked.\n\nError: {exc}\n\n"
                f"Stop and report this error to the user. Do not attempt to write the file again "
                f"until the subprocess issue is resolved."
            )
            return False
        if decision.additional_context:
            gate.warn(decision.additional_context)
        if not decision.allow:
            gate.log(f"DENY {file_name}: {decision.reason}")
            gate.block(decision.reason or "[health-check] Review did not authorize the write.")
            return False
        return True
