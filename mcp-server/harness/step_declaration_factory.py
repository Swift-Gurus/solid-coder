"""Creates workflow-step declarations from structured input."""

from __future__ import annotations

from harness.output_spec_creating import OutputSpecCreating
from harness.step_declaration import StepDeclaration
from harness.step_declaration_mapping import StepDeclarationMapping


"""
solid-name: StepDeclarationFactory
solid-category: factory
solid-spec: [SPEC-027, SPEC-030, SPEC-035]
solid-description: Creates unvalidated workflow-step declarations from structured input.
"""
class StepDeclarationFactory(StepDeclarationMapping):
    def __init__(self, output_factory: OutputSpecCreating) -> None:
        self._output_factory = output_factory

    def map(self, raw: dict) -> StepDeclaration:
        outputs = [
            self._output_factory.create(
                name=output["name"],
                output_type=output["type"],
                schema=output.get("schema"),
                schema_file=output.get("schema_file"),
            )
            for output in raw.get("outputs") or []
        ]
        return StepDeclaration(
            id=raw.get("id"),
            type=raw.get("type", "agent"),
            prompt=raw.get("prompt"),
            depends_on=raw.get("depends_on"),
            outputs=outputs,
            for_each=raw.get("for_each"),
            mode=raw.get("mode"),
            prompt_file=raw.get("prompt_file"),
            command=raw.get("command"),
            script_file_reference=raw.get("file"),
            script_file=raw.get("script_file"),
            executor=raw.get("executor"),
            args=raw.get("args"),
            timeout_seconds=raw.get("timeout_seconds"),
            max_attempts=raw.get("max_attempts", 3),
            source_file=raw.get("__source_file"),
        )
