"""
solid-description: Loads and fully validates flow definitions from files.
solid-category: service
"""

from __future__ import annotations

from pathlib import Path

from scoring.yaml_config_file_loader import ConfigFileLoading
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.command_allowlist_validating import CommandAllowlistValidating
from harness.flow_loading import FlowLoading
from harness.group_dependency_expanding import GroupDependencyExpanding
from harness.include_resolving import IncludeResolving
from harness.models import FlowDef, FlowValidationError
from harness.output_schema_prompt_annotating import OutputSchemaPromptAnnotating
from harness.output_schema_resolving import OutputSchemaResolving
from harness.prompt_content_resolving import PromptContentResolving
from harness.uses_resolver import UsesResolving
from harness.flow_graph_validator import FlowGraphValidating
from harness.step_building import StepBuilding
from harness.step_shape_validating import StepShapeValidating
from harness.flow_config_extractor import FlowConfigExtracting


class FlowLoader(FlowLoading):
    """
    solid-description: Loads and fully validates flow definitions from files.
    solid-category: service
    """

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        config_extractor: FlowConfigExtracting,
        uses_resolver: UsesResolving,
        graph_validator: FlowGraphValidating,
        step_builder: StepBuilding,
        include_resolver: IncludeResolving,
        step_shape_validator: StepShapeValidating,
        prompt_content_resolver: PromptContentResolving,
        output_schema_resolver: OutputSchemaResolving,
        output_schema_prompt_annotator: OutputSchemaPromptAnnotating,
        command_allowlist_resolver: CommandAllowlistResolving,
        command_allowlist_validator: CommandAllowlistValidating,
        group_dependency_expander: GroupDependencyExpanding,
    ) -> None:
        self._file_loader = file_loader
        self._config_extractor = config_extractor
        self._uses_resolver = uses_resolver
        self._graph_validator = graph_validator
        self._step_builder = step_builder
        self._include_resolver = include_resolver
        self._step_shape_validator = step_shape_validator
        self._prompt_content_resolver = prompt_content_resolver
        self._output_schema_resolver = output_schema_resolver
        self._output_schema_prompt_annotator = output_schema_prompt_annotator
        self._command_allowlist_resolver = command_allowlist_resolver
        self._command_allowlist_validator = command_allowlist_validator
        self._group_dependency_expander = group_dependency_expander

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        raw = self._file_loader.load(Path(path))
        if raw is None:
            raise FlowValidationError(f"Flow file not found or unreadable: '{path}'")

        name = self._config_extractor.extract_name(raw)
        max_turns = self._config_extractor.extract_max_turns(raw)
        raw_steps = self._config_extractor.extract_steps(raw)

        resolved_steps = [
            self._uses_resolver.resolve(step, path, search_paths)
            for step in raw_steps
        ]
        top_level_step_ids = {s["id"] for s in resolved_steps if "id" in s}

        inclusion = self._include_resolver.resolve(resolved_steps, path)
        self._step_shape_validator.validate(inclusion.steps)

        steps_with_prompts = [
            self._prompt_content_resolver.resolve(step, path)
            for step in inclusion.steps
        ]
        steps_with_schemas = [
            self._output_schema_resolver.resolve(step, path)
            for step in steps_with_prompts
        ]
        steps_with_annotated_prompts = [
            self._output_schema_prompt_annotator.annotate(step)
            for step in steps_with_schemas
        ]

        allowlist = self._command_allowlist_resolver.resolve()
        self._command_allowlist_validator.validate(steps_with_annotated_prompts, allowlist)

        self._graph_validator.validate_raw(steps_with_annotated_prompts, inclusion.alias_groups)
        self._graph_validator.validate_includes(
            steps_with_annotated_prompts, inclusion.alias_groups, top_level_step_ids, inclusion.include_chain
        )

        fully_expanded_steps = self._group_dependency_expander.expand(steps_with_annotated_prompts, inclusion.alias_groups)

        steps = [self._step_builder.build(s) for s in fully_expanded_steps]
        self._graph_validator.validate_for_each_references(steps)

        return FlowDef(name=name, max_turns=max_turns, steps=steps)
