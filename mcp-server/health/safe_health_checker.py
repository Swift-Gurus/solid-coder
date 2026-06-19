"""
solid-description: Safely invokes the health checker and translates subprocess errors into gate block decisions.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HEALTH_DIR.parents[1] / 'hooks'
for _d in (_HOOKS_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from gate_protocols import GateHandling, HealthChecking, ViolationFormatting


class SafeHealthChecker:
    """Invokes the health checker, handles errors, and returns True if the content is clean."""

    def __init__(self, checker: HealthChecking, formatter: ViolationFormatting) -> None:
        self._checker = checker
        self._formatter = formatter

    def check(self, content: str, path: str, language: str, session_id: str, gate: GateHandling, file_name: str) -> bool:
        try:
            violations = self._checker.check(content, path, language, session_id)
        except Exception as exc:
            gate.log(f"BLOCK {file_name}: health subprocess error: {exc}")
            gate.block(
                f"[health-check] Gate subprocess failed — the write is blocked.\n\nError: {exc}\n\n"
                f"Stop and report this error to the user. Do not attempt to write the file again "
                f"until the subprocess issue is resolved."
            )
            return False
        if violations:
            gate.log(f"DENY {file_name}: {len(violations)} violation(s)")
            parts = [
                self._formatter.format_block_reason(violations),
                "The file was NOT written. You MUST fix all violations above and write the corrected version before continuing.",
            ]
            gate.block("[health-check] " + "\n\n".join(parts))
            return False
        return True
