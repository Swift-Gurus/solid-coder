"""Validates pipeline architecture and findings artifacts."""

from pipeline.pipeline_validation_handling import PipelineValidationHandling
from pipeline.skill_runner import ResultFormatting, SkillRunning
from utils.path_file_system_reader import FileSystemReading


"""
solid-name: PipelineValidationHandler
solid-category: validator
solid-description: Validates architecture plans and scored review findings through pipeline commands.
"""
class PipelineValidationHandler(PipelineValidationHandling):
    def __init__(
        self,
        runner: SkillRunning,
        formatter: ResultFormatting,
        file_system: FileSystemReading,
        skills_root: str,
        plugin_root: str,
    ) -> None:
        self._runner = runner
        self._formatter = formatter
        self._file_system = file_system
        self._skills_root = skills_root
        self._plugin_root = plugin_root

    def validate_architecture(self, arch_path: str) -> dict:
        plan_root = self._file_system.subpath(self._skills_root, "plan")
        schema = self._file_system.subpath(plan_root, "arch.schema.json")
        succeeded, output, error = self._runner.execute(
            "plan",
            "validate-arch.py",
            [arch_path, "--schema", schema],
        )
        return self._formatter.format(
            succeeded,
            error,
            valid=succeeded,
            output=output,
            errors=error if not succeeded else None,
        )

    def validate_findings(self, output_root: str) -> dict:
        succeeded, output, error = self._runner.execute(
            "validate-findings",
            "validate-findings.py",
            [output_root, self._plugin_root],
        )
        return self._formatter.format(
            succeeded,
            error,
            success=succeeded,
            output=output,
        )
