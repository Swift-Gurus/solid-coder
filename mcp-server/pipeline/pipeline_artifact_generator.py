"""Generates pipeline plan and report artifacts."""

from typing import Optional

from pipeline.pipeline_artifact_generating import PipelineArtifactGenerating
from pipeline.skill_runner import ResultFormatting, SkillRunning
from utils.path_file_system_reader import FileSystemReading


"""
solid-name: PipelineArtifactGenerator
solid-category: service
solid-description: Generates implementation-plan chunks and model-facing review reports.
"""
class PipelineArtifactGenerator(PipelineArtifactGenerating):
    def __init__(
        self,
        runner: SkillRunning,
        formatter: ResultFormatting,
        file_system: FileSystemReading,
    ) -> None:
        self._runner = runner
        self._formatter = formatter
        self._file_system = file_system

    def split_implementation_plan(
        self,
        plan_path: str,
        output_dir: str,
        arch_path: Optional[str] = None,
    ) -> dict:
        arguments = [plan_path, "--output-dir", output_dir]
        if arch_path:
            arguments += ["--arch", arch_path]
        succeeded, output, error = self._runner.execute(
            "synthesize-implementation",
            "split-plan.py",
            arguments,
        )
        chunks = self._file_system.glob(output_dir, "*.json") if succeeded else []
        return self._formatter.format(
            succeeded,
            error,
            success=succeeded,
            chunks=sorted(str(chunk) for chunk in chunks),
            count=len(chunks),
        )

    def generate_report(
        self,
        data_dir: str,
        report_dir: Optional[str] = None,
    ) -> dict:
        destination = report_dir or data_dir
        succeeded, output, error = self._runner.execute(
            "generate-report",
            "generate-report.py",
            [data_dir, destination],
        )
        return self._formatter.format(
            succeeded,
            error,
            success=succeeded,
            md_path=(
                self._file_system.subpath(destination, "report.md")
                if succeeded
                else None
            ),
            html_path=(
                self._file_system.subpath(destination, "report.html")
                if succeeded
                else None
            ),
        )
