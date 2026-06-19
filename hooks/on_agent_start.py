"""
solid-description: Registers session identity, type, and working directory from provided input.
solid-category: service
solid-tags: [hook]
"""

import json
import os
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _HOOKS_DIR / "session"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from session_registry import register_session  # noqa: E402

_SESSION_TYPE_ENV = "SOLID_CODER_SESSION_TYPE"


def main() -> None:
    session_type = os.environ.get(_SESSION_TYPE_ENV, "").strip()
    if not session_type:
        sys.exit(0)

    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    session_id = event.get("session_id", "")
    cwd = event.get("cwd", os.getcwd())
    if not session_id:
        sys.exit(0)

    register_session(session_id=session_id, session_type=session_type, cwd=cwd)


if __name__ == "__main__":
    main()
