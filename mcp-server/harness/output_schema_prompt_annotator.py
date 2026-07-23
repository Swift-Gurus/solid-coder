"""
solid-name: OutputSchemaPromptAnnotator
solid-category: service
solid-spec: [SPEC-027]
solid-description: Augments steps with output schema specifications.
"""

from __future__ import annotations

import json

from harness.output_schema_prompt_annotating import OutputSchemaPromptAnnotating

_SCRIPT_STEP_TYPE = "script"


class OutputSchemaPromptAnnotator(OutputSchemaPromptAnnotating):

    def annotate(self, step: dict) -> dict:
        if step.get("type", "agent") == _SCRIPT_STEP_TYPE:
            return step

        prompt = step.get("prompt", "")
        descriptions = [
            self._describe(output)
            for output in step.get("outputs") or []
            if output.get("schema") is not None
        ]
        new_lines = [line for line in descriptions if line not in prompt]
        if not new_lines:
            return step

        resolved = dict(step)
        resolved["prompt"] = "\n\n".join([prompt, *new_lines])
        return resolved

    def _describe(self, output: dict) -> str:
        return f"Submit output '{output['name']}' matching this schema: {json.dumps(output['schema'])}"
