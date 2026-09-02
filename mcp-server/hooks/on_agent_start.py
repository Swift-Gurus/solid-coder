"""
solid-description: Registers session identity, type, and working directory from provided input.
solid-category: service
solid-tags: [hook]
"""

import json
import os
import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[1]
for _d in (_MCP_DIR, _MCP_DIR / "session"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from session_registry import register_session  # noqa: E402
from session_project_context_path_resolver import (  # noqa: E402
    SessionProjectContextPathResolver,
)
from session_project_directory_recorder import (  # noqa: E402
    SessionProjectDirectoryRecorder,
)

_SESSION_TYPE_ENV = "SOLID_CODER_SESSION_TYPE"


def main() -> None:
    session_type = os.environ.get(_SESSION_TYPE_ENV, "").strip()

    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    session_id = event.get("session_id", "")
    cwd = event.get("cwd", os.getcwd())
    if not session_id:
        sys.exit(0)

    SessionProjectDirectoryRecorder(
        SessionProjectContextPathResolver().resolve
    ).record(session_id, Path(cwd))
    if not session_type:
        return

    register_session(session_id=session_id, session_type=session_type, cwd=cwd)


if __name__ == "__main__":
    main()
