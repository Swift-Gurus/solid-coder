"""
solid-description: Builds a codex execution command with configured model and profile.
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

from pathlib import Path


class CodexCommandBuilder:
    """Builds the codex exec command list for a health-check session."""

    def __init__(self, model: str, profile_name: str) -> None:
        self._model = model
        self._profile_name = profile_name

    def build(self, result_path: Path) -> list:
        """Return the codex exec command, parameterized by output file path."""
        cmd = [
            "codex", "exec",
            "--json",
            "--dangerously-bypass-approvals-and-sandbox",
            "--dangerously-bypass-hook-trust",
            "--skip-git-repo-check",
            "--profile", self._profile_name,
            "--output-last-message", str(result_path),
            "-",
        ]
        if self._model:
            cmd += ["--model", self._model]
        return cmd
