"""Coordinates role-focused pipeline command operations."""

from typing import Optional

from pipeline.pipeline_artifact_generating import PipelineArtifactGenerating
from pipeline.pipeline_command_handling import PipelineCommandHandling
from pipeline.pipeline_validation_handling import PipelineValidationHandling
from pipeline.review_input_preparing import ReviewInputPreparing


"""
solid-name: PipelineCommandHandler
solid-category: service
solid-description: Coordinates preparation, artifact generation, and validation commands exposed by the pipeline.
"""
class PipelineCommandHandler(PipelineCommandHandling):
    def __init__(
        self,
        review_input: ReviewInputPreparing,
        artifacts: PipelineArtifactGenerating,
        validation: PipelineValidationHandling,
    ) -> None:
        self._review_input = review_input
        self._artifacts = artifacts
        self._validation = validation

    def prepare_review_input(self, candidate_tags=None) -> dict:
        return self._review_input.prepare(candidate_tags)

    def split_implementation_plan(
        self,
        plan_path: str,
        output_dir: str,
        arch_path: Optional[str] = None,
    ) -> dict:
        return self._artifacts.split_implementation_plan(
            plan_path,
            output_dir,
            arch_path,
        )

    def generate_report(
        self,
        data_dir: str,
        report_dir: Optional[str] = None,
    ) -> dict:
        return self._artifacts.generate_report(data_dir, report_dir)

    def validate_architecture(self, arch_path: str) -> dict:
        return self._validation.validate_architecture(arch_path)

    def validate_findings(self, output_root: str) -> dict:
        return self._validation.validate_findings(output_root)
