"""Appends ordinary steps to include resolutions."""

from dataclasses import replace

from harness.include_resolution import IncludeResolution
from harness.include_step_appending import IncludeStepAppending


"""
solid-name: IncludeStepAppender
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Appends a non-include step to an include resolution.
"""
class IncludeStepAppender(IncludeStepAppending):

    def append(self, resolution: IncludeResolution, step: dict) -> IncludeResolution:
        return replace(
            resolution,
            steps=[*resolution.steps, step],
        )
