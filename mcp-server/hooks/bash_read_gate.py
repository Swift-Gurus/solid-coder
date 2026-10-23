"""
solid-description: Validates whether source file reads comply with access policy.
solid-category: service
solid-tags: [hook]
"""

import re
from pathlib import Path

from logging_protocol import Logging


class BashReadGate:
    """Detects Bash commands that read source files instead of using the Read tool.

    Blocks cat/head/tail when used with a source file argument.
    Allows: heredocs (cat <<'EOF'), pipeline targets (cmd | head), /dev/* paths.
    """

    _SOURCE_EXTENSIONS = (
        ".py",
        ".swift",
        ".kt",
        ".java",
        ".js",
        ".ts",
        ".json",
        ".md",
        ".toml",
        ".yaml",
        ".yml",
        ".sh",
    )

    def __init__(self, logger: Logging) -> None:
        self._logger = logger

    def _looks_like_source_file(self, command: str) -> bool:
        if not any(ext in command for ext in self._SOURCE_EXTENSIONS):
            return False
        # Only block files that resolve to inside the current project root.
        # Absolute paths outside the project (e.g. /tmp/, ~/Downloads/) are allowed.
        project_root = Path.cwd().resolve()
        for token in command.split():
            if not any(token.endswith(ext) for ext in self._SOURCE_EXTENSIONS):
                continue
            try:
                resolved = Path(token).resolve()
                if not str(resolved).startswith(str(project_root)):
                    return False  # outside the project — allow
            except Exception as exc:  # noqa: BLE001 — Disabled legacy source-read gate retains its logged resolution fallback for re-enabling.
                self._logger.log(
                    f"Failed to resolve Bash source path: path={token}; treating as project file; "
                    f"{type(exc).__name__}: {exc}"
                )
        return True

    def _is_heredoc(self, command: str) -> bool:
        return "<<" in command

    def _is_devnull_or_special(self, command: str) -> bool:
        return "/dev/" in command

    def _is_pipeline_target(self, command: str, cmd_name: str) -> bool:
        return bool(re.search(rf"\|\s*{cmd_name}\b", command))

    def check(self, command: str) -> str | None:
        """Return the read-command name if it reads a source file, else None."""
        if not self._looks_like_source_file(command):
            return None
        if self._is_heredoc(command) or self._is_devnull_or_special(command):
            return None
        for cmd_name in ("cat", "head", "tail"):
            if not re.search(rf"\b{cmd_name}\b", command):
                continue
            if self._is_pipeline_target(command, cmd_name):
                continue
            return cmd_name
        return None
