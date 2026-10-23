"""Defines generation of pipeline plans and reports."""

from typing import Protocol

"""
solid-name: PipelineArtifactGenerating
solid-category: abstraction
solid-description: Contract for generating implementation-plan chunks and review report artifacts.
"""


class PipelineArtifactGenerating(Protocol):
    def split_implementation_plan(
        self,
        plan_path: str,
        output_dir: str,
        arch_path: str | None = None,
    ) -> dict: ...

    def generate_report(
        self,
        data_dir: str,
        report_dir: str | None = None,
    ) -> dict: ...
