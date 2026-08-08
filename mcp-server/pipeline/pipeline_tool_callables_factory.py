"""Builds the callable map exposed by the pipeline MCP server."""

from typing import Any, Callable

from health.dry_search_coordinating import DrySearchCoordinating
from pipeline.output_path_computing import OutputPathComputing
from pipeline.pipeline_command_handling import PipelineCommandHandling
from pipeline.tool_callables_building import ToolCallablesBuilding


"""
solid-name: PipelineToolCallablesFactory
solid-category: factory
solid-description: Builds the model-facing pipeline callable registry from role-focused operations.
"""
class PipelineToolCallablesFactory(ToolCallablesBuilding):
    def __init__(
        self,
        commands: PipelineCommandHandling,
        dry_search: DrySearchCoordinating,
        collect_review_results: Callable[[str], Any],
        check_severity: Callable[[str], dict],
        load_context: Callable[[str], dict],
        validate_json: Callable[[str, str], dict],
        submit_findings: Callable[[dict, str], dict],
        submit_batch_findings: Callable[[str, object], dict],
        submit_fix: Callable[[str, list], dict],
        output_path: OutputPathComputing,
    ) -> None:
        self._commands = commands
        self._dry_search = dry_search
        self._collect_review_results = collect_review_results
        self._check_severity = check_severity
        self._load_context = load_context
        self._validate_json = validate_json
        self._submit_findings = submit_findings
        self._submit_batch_findings = submit_batch_findings
        self._submit_fix = submit_fix
        self._output_path = output_path

    def build(self) -> dict:
        return {
            "collect_review_results": self._collect_review_results,
            "check_severity": self._check_severity,
            "validate_findings": self._commands.validate_findings,
            "load_synthesis_context": self._load_context,
            "generate_report": self._commands.generate_report,
            "validate_architecture": self._commands.validate_architecture,
            "split_implementation_plan": self._commands.split_implementation_plan,
            "search_codebase": self._dry_search.search,
            "prepare_review_input": self._commands.prepare_review_input,
            "validate_phase_output": self._validate_json,
            "submit_findings": self._submit_findings,
            "submit_batch_findings": self._submit_batch_findings,
            "submit_fix": self._submit_fix,
            "get_output_path": self._output_path.compute,
        }
