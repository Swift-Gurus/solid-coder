"""Resolves script files declared by workflow steps."""

from harness.resolved_script_file_applying import ResolvedScriptFileApplying
from harness.script_file_resolving import ScriptFileResolving
from harness.step_declaration import StepDeclaration
from harness.step_declaring_file_resolving import StepDeclaringFileResolving
from harness.workflow_resource_path_resolving import WorkflowResourcePathResolving
from harness.workflow_resource_reference_creating import WorkflowResourceReferenceCreating


"""
solid-name: ScriptFileResolver
solid-category: service
solid-spec: [SPEC-035]
solid-description: Resolves a workflow step's script-file reference into a contained executable filesystem path.
"""
class ScriptFileResolver(ScriptFileResolving):
    def __init__(
        self,
        declaring_file_resolver: StepDeclaringFileResolving,
        resource_path_resolver: WorkflowResourcePathResolving,
        reference_factory: WorkflowResourceReferenceCreating,
        script_file_applier: ResolvedScriptFileApplying,
    ) -> None:
        self._declaring_file_resolver = declaring_file_resolver
        self._resource_path_resolver = resource_path_resolver
        self._reference_factory = reference_factory
        self._script_file_applier = script_file_applier

    def resolve(
        self,
        step: StepDeclaration,
        flow_file_path: str,
    ) -> StepDeclaration:
        declared_file = step.script_file_reference
        if not isinstance(declared_file, str):
            return step

        declaring_file = self._declaring_file_resolver.resolve(
            step.source_file,
            flow_file_path,
        )
        reference = self._reference_factory.create(declared_file)
        resolved_path = self._resource_path_resolver.resolve(declaring_file, reference)
        return self._script_file_applier.apply(step, str(resolved_path))
