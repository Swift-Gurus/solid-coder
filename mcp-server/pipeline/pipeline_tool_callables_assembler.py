"""Assembles role-focused pipeline tool callables."""

from pathlib import Path
from typing import Any, Callable

from health.dry_search_coordinating import DrySearchCoordinating
from health.llama.json_deserializer import JsonDeserializer
from pipeline.output_path_computing import OutputPathComputing
from pipeline.pipeline_artifact_generator import PipelineArtifactGenerator
from pipeline.pipeline_command_handler import PipelineCommandHandler
from pipeline.pipeline_tool_callables_factory import PipelineToolCallablesFactory
from pipeline.pipeline_validation_handler import PipelineValidationHandler
from pipeline.review_input_preparer import ReviewInputPreparer
from pipeline.skill_runner import ResultFormatting, SkillRunning
from pipeline.tool_callables_building import ToolCallablesBuilding
from utils.path_file_system_reader import PathFileSystemReader


"""
solid-name: PipelineToolCallablesAssembler
solid-category: factory
solid-description: Assembles role-focused operations into the model-facing pipeline callable registry.
"""
class PipelineToolCallablesAssembler(ToolCallablesBuilding):
    def __init__(
        self,
        runner: SkillRunning,
        formatter: ResultFormatting,
        dry_search: DrySearchCoordinating,
        collect_review_results: Callable[[str], Any],
        check_severity: Callable[[str], dict],
        load_context: Callable[[str], dict],
        validate_json: Callable[[str, str], dict],
        submit_findings: Callable[[dict, str], dict],
        submit_batch_findings: Callable[[str, object], dict],
        submit_fix: Callable[[str, list], dict],
        output_path: OutputPathComputing,
        skills_root: Path,
        plugin_root: Path,
    ) -> None:
        file_system = PathFileSystemReader()
        commands = PipelineCommandHandler(
            review_input=ReviewInputPreparer(runner, JsonDeserializer()),
            artifacts=PipelineArtifactGenerator(runner, formatter, file_system),
            validation=PipelineValidationHandler(
                runner,
                formatter,
                file_system,
                str(skills_root),
                str(plugin_root),
            ),
        )
        self._callables = PipelineToolCallablesFactory(
            commands=commands,
            dry_search=dry_search,
            collect_review_results=collect_review_results,
            check_severity=check_severity,
            load_context=load_context,
            validate_json=validate_json,
            submit_findings=submit_findings,
            submit_batch_findings=submit_batch_findings,
            submit_fix=submit_fix,
            output_path=output_path,
        )

    def build(self) -> dict:
        return self._callables.build()
