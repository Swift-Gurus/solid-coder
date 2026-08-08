"""Validates completed Codex subprocess executions."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating


"""
solid-name: CodexExecutionValidator
solid-category: service
solid-description: Rejects unsuccessful Codex execution outcomes with available diagnostics.
solid-tags: [hook, llm]
"""
class CodexExecutionValidator:
    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, succeeded: bool, stdout: str, stderr: str) -> None:
        if succeeded:
            return
        detail = stderr[:300] or stdout[:300]
        raise self._error_factory.create(f"`codex exec` exited with error: {detail}")
