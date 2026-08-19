"""Defines validated read-only Git queries."""

from pathlib import Path
from typing import Protocol

from source.git_process_execution import GitProcessExecution


"""
solid-name: GitQuerying
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for executing validated read-only Git queries for a project.
"""
class GitQuerying(Protocol):
    def query(
        self,
        project_root: Path,
        execution: GitProcessExecution,
        purpose: str,
    ) -> str: ...
