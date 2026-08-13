"""Applies resolved resources to workflow steps."""

from dataclasses import replace

from harness.resolved_step_resources import ResolvedStepResources
from harness.resolved_step_resources_applying import ResolvedStepResourcesApplying
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedStepResourcesApplier
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Applies resolved resources to a workflow-step declaration.
"""
class ResolvedStepResourcesApplier(ResolvedStepResourcesApplying):

    def apply(
        self,
        step: StepDeclaration,
        resources: ResolvedStepResources,
    ) -> StepDeclaration:
        return replace(
            step,
            prompt=resources.prompt,
            prompt_file=resources.prompt_file,
            script_file_reference=resources.script_file_reference,
            script_file=resources.script_file,
            outputs=resources.outputs,
        )
