"""Builds executable workflow step definitions."""

from __future__ import annotations

from typing import cast

from harness.for_each_declaration import ForEachDeclaration
from harness.output_spec import OutputSpec
from harness.step_declaration import StepDeclaration
from harness.step_def import StepDef

"""
solid-name: StepBuilder
solid-category: service
solid-spec: [SPEC-027, SPEC-030, SPEC-035, SPEC-037, SPEC-039]
solid-description: Constructs executable workflow-step specifications from validated workflow declarations.
"""


class StepBuilder:
    def build(self, declaration: StepDeclaration) -> StepDef:
        return StepDef(
            id=cast(str, declaration.id),
            prompt=cast(str, declaration.prompt or ""),
            authored_prompt=cast(
                str,
                declaration.authored_prompt or declaration.prompt or "",
            ),
            depends_on=cast(list[str], declaration.depends_on or []),
            outputs=cast(list[OutputSpec], declaration.outputs or []),
            for_each=cast(ForEachDeclaration | None, declaration.for_each),
            condition=declaration.condition,
            type=cast(str, declaration.type),
            mode=cast(str | None, declaration.mode),
            prompt_file=cast(str | None, declaration.prompt_file),
            command=cast(list[str] | str | None, declaration.command),
            script_file=cast(str | None, declaration.script_file),
            executor=cast(str | None, declaration.executor),
            args=cast(list[str] | None, declaration.args),
            timeout_seconds=cast(int | None, declaration.timeout_seconds),
            max_attempts=cast(int, declaration.max_attempts),
            metric=declaration.metric,
            metric_calculation=declaration.metric_calculation,
            assessment=declaration.assessment,
            operation=declaration.operation,
        )
