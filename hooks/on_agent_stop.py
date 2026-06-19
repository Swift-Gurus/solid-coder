"""
solid-description: Validates session termination prerequisites and exits with error if validation fails.
solid-category: service
solid-tags: [hook]
"""

import json
import os
import sys
from pathlib import Path
from typing import Callable, Optional

_HOOKS_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _HOOKS_DIR / "session"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from session_registry import validate_session_stop  # noqa: E402


class SessionStopGate:
    """Validates a Stop event and exits with code 2 if required tools were not called."""

    def __init__(self, validate_fn: Callable) -> None:
        self._validate = validate_fn

    def run(self, raw: str) -> None:
        try:
            event = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return
        if event.get("stop_hook_active"):
            return
        session_id = event.get("session_id", "")
        if not session_id:
            return
        transcript_path: Optional[str] = event.get("transcript_path") or None
        cwd = event.get("cwd", os.getcwd())
        result = self._validate(session_id=session_id, transcript_path=transcript_path, cwd=cwd)
        if not result.get("allow", True):
            sys.stderr.write(result.get("reason", "Required MCP tools were not called."))
            sys.stderr.flush()
            sys.exit(2)


def main() -> None:
    SessionStopGate(validate_fn=validate_session_stop).run(sys.stdin.read())


if __name__ == "__main__":
    main()
