"""
solid-description: Transforms input data into executable step specifications.
solid-category: service
"""

from __future__ import annotations

from harness.models import OutputSpec, StepDef


class StepBuilder:
    """
    solid-description: Transforms input data into executable step specifications.
    solid-category: service
    """

    def build(self, raw: dict) -> StepDef:
        raw_outputs = raw.get("outputs") or []
        outputs = [
            OutputSpec(
                name=o["name"],
                type=o["type"],
                schema=o.get("schema"),
                schema_file=o.get("schema_file"),
            )
            for o in raw_outputs
        ]

        return StepDef(
            id=raw["id"],
            prompt=raw.get("prompt") or "",
            depends_on=raw.get("depends_on") or [],
            outputs=outputs,
            for_each=raw.get("for_each"),
            type=raw.get("type", "agent"),
            mode=raw.get("mode"),
            prompt_file=raw.get("prompt_file"),
            command=raw.get("command"),
            timeout_seconds=raw.get("timeout_seconds"),
            max_attempts=raw.get("max_attempts", 3),
        )
