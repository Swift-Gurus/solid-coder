"""Defines pipeline command operations exposed through the callable registry."""

from typing import Optional, Protocol


"""
solid-name: PipelineCommandHandling
solid-category: abstraction
solid-description: Contract for executing and formatting pipeline preparation, validation, planning, and reporting commands.
"""
class PipelineCommandHandling(Protocol):
    def prepare_review_input(self, candidate_tags=None) -> dict: ...

    def split_implementation_plan(
        self,
        plan_path: str,
        output_dir: str,
        arch_path: Optional[str] = None,
    ) -> dict: ...

    def generate_report(
        self,
        data_dir: str,
        report_dir: Optional[str] = None,
    ) -> dict: ...

    def validate_architecture(self, arch_path: str) -> dict: ...

    def validate_findings(self, output_root: str) -> dict: ...
