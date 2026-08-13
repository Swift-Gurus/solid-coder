"""Creates workflow-step resource snapshots."""

from harness.resolved_step_resources import ResolvedStepResources
from harness.resolved_step_resources_creating import ResolvedStepResourcesCreating
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedStepResourcesFactory
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Creates a resource snapshot from a workflow-step declaration.
"""
class ResolvedStepResourcesFactory(ResolvedStepResourcesCreating):

    def create(self, step: StepDeclaration) -> ResolvedStepResources:
        return ResolvedStepResources(
            prompt=step.prompt,
            prompt_file=step.prompt_file,
            script_file_reference=step.script_file_reference,
            script_file=step.script_file,
            outputs=step.outputs,
        )
