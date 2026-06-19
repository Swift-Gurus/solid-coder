"""
solid-description: Synchronizes authentication credentials between the system installation and a managed directory.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_HOOKS_DIR = Path(__file__).resolve().parents[3] / 'hooks'
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import os
import shutil
from pathlib import Path


class CodexAuthSyncer:
    """Copies auth.json from the system CODEX_HOME so a managed home can authenticate."""

    def sync(self, codex_home: str) -> None:
        """Copy auth.json from the system CODEX_HOME if it exists and the target does not."""
        default_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        auth_src = default_home / "auth.json"
        auth_dst = Path(codex_home) / "auth.json"
        if auth_src.exists() and not auth_dst.exists():
            shutil.copy2(auth_src, auth_dst)
