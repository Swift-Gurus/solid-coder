"""Applies resolved script paths to workflow steps."""

from harness.resolved_script_file_applying import ResolvedScriptFileApplying
from harness.resolved_step_resources_applying import ResolvedStepResourcesApplying
from harness.resolved_step_resources_creating import ResolvedStepResourcesCreating
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedScriptFileApplier
solid-category: service
solid-spec: [SPEC-035]
solid-description: Applies a resolved script path to a workflow-step declaration.
"""
class ResolvedScriptFileApplier(ResolvedScriptFileApplying):

    def __init__(
        self,
        resources_factory: ResolvedStepResourcesCreating,
        resources_applier: ResolvedStepResourcesApplying,
    ) -> None:
        self._resources_factory = resources_factory
        self._resources_applier = resources_applier

    def apply(
        self,
        step: StepDeclaration,
        script_file: str,
    ) -> StepDeclaration:
        resources = self._resources_factory.create(step)
        resources.script_file_reference = None
        resources.script_file = script_file
        return self._resources_applier.apply(step, resources)
