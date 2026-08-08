"""Validates requested health-check context directory ownership."""

from findings.hook_context import HookContext
from findings.hook_context_ownership_validating import HookContextOwnershipValidating
from harness.path_building import PathBuilding


"""
solid-name: HookContextOwnershipValidator
solid-category: validator
solid-description: Verifies hook context resolves to the output directory that requested it.
"""
class HookContextOwnershipValidator(HookContextOwnershipValidating):
    def __init__(self, path_builder: PathBuilding) -> None:
        self._path_builder = path_builder

    def is_owned(self, context: HookContext, output_dir: str) -> bool:
        return context.output_directory == self._path_builder.build(output_dir)
