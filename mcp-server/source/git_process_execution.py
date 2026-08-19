"""Defines one read-only Git process request."""

from dataclasses import dataclass, field


"""
solid-name: GitProcessExecution
solid-category: model
solid-spec: [SPEC-040]
solid-description: Represents an ordered read-only Git invocation request.
"""
@dataclass(frozen=True)
class GitProcessExecution:
    arguments: list[str] = field(default_factory=list)

    def process_arguments(self) -> list[str]:
        return ["git", *self.arguments]
