"""Applies resolved outputs to workflow steps."""

from harness.output_spec import OutputSpec
from harness.resolved_outputs_applying import ResolvedOutputsApplying
from harness.resolved_step_resources_applying import ResolvedStepResourcesApplying
from harness.resolved_step_resources_creating import ResolvedStepResourcesCreating
from harness.step_declaration import StepDeclaration


"""
solid-name: ResolvedOutputsApplier
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Applies resolved outputs to a workflow-step declaration.
"""
class ResolvedOutputsApplier(ResolvedOutputsApplying):

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
        outputs: list[OutputSpec],
    ) -> StepDeclaration:
        resources = self._resources_factory.create(step)
        resources.outputs = outputs
        return self._resources_applier.apply(step, resources)
