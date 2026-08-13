"""Builds executable workflow step definitions."""

from __future__ import annotations

from typing import Optional, Union, cast

from harness.output_spec import OutputSpec
from harness.step_declaration import StepDeclaration
from harness.step_def import StepDef


"""
solid-name: StepBuilder
solid-category: service
solid-spec: [SPEC-027, SPEC-030, SPEC-035]
solid-description: Constructs executable workflow-step specifications from validated workflow declarations.
"""
class StepBuilder:
    def build(self, declaration: StepDeclaration) -> StepDef:
        return StepDef(
            id=cast(str, declaration.id),
            prompt=cast(str, declaration.prompt or ""),
            depends_on=cast(list[str], declaration.depends_on or []),
            outputs=cast(list[OutputSpec], declaration.outputs or []),
            for_each=cast(Optional[str], declaration.for_each),
            type=cast(str, declaration.type),
            mode=cast(Optional[str], declaration.mode),
            prompt_file=cast(Optional[str], declaration.prompt_file),
            command=cast(Union[list[str], str, None], declaration.command),
            script_file=cast(Optional[str], declaration.script_file),
            executor=cast(Optional[str], declaration.executor),
            args=cast(Optional[list[str]], declaration.args),
            timeout_seconds=cast(Optional[int], declaration.timeout_seconds),
            max_attempts=cast(int, declaration.max_attempts),
        )
