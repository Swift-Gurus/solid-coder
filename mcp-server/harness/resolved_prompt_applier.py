"""Applies resolved prompt content to workflow steps."""

from harness.resolved_prompt_applying import ResolvedPromptApplying
from harness.resolved_step_resources_applying import ResolvedStepResourcesApplying
from harness.resolved_step_resources_creating import ResolvedStepResourcesCreating
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedPromptApplier
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Applies resolved prompt content to a workflow-step declaration.
"""
class ResolvedPromptApplier(ResolvedPromptApplying):

    def __init__(
        self,
        resources_factory: ResolvedStepResourcesCreating,
        resources_applier: ResolvedStepResourcesApplying,
    ) -> None:
        self._resources_factory = resources_factory
        self._resources_applier = resources_applier

    def apply(self, step: StepDeclaration, prompt: str) -> StepDeclaration:
        resources = self._resources_factory.create(step)
        resources.prompt = prompt
        resources.prompt_file = None
        return self._resources_applier.apply(step, resources)
