"""Provides a reusable real Git working tree for source-operation tests."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitWorkingTreeFixture:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def initialize(self) -> None:
        self.run("init")
        self.run("config", "user.email", "test@example.com")
        self.run("config", "user.name", "Test")

    def write(self, path: str, content: str) -> None:
        (self.project_root / path).write_text(content, encoding="utf-8")

    def remove(self, path: str) -> None:
        (self.project_root / path).unlink()

    def run(self, *arguments: str) -> None:
        self._require_success(self._execute(list(arguments)))

    def output(self, *arguments: str) -> str:
        result = self._execute(list(arguments))
        self._require_success(result)
        return result.stdout

    def _execute(
        self,
        arguments: list[str],
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

    @staticmethod
    def _require_success(result: subprocess.CompletedProcess[str]) -> None:
        if result.returncode != 0:
            raise AssertionError(result.stderr)
