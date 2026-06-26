"""
solid-description: Loads and validates a flow definition from a YAML file.
solid-category: service
"""

from __future__ import annotations

from pathlib import Path

from scoring.yaml_config_file_loader import YamlConfigFileLoader
from harness.flow_loading import FlowLoading
from harness.models import FlowDef, FlowValidationError
from harness.uses_resolver import UsesResolving
from harness.flow_graph_validator import FlowGraphValidating
from harness.step_builder import StepBuilding
from harness.flow_config_extractor import FlowConfigExtracting


class FlowLoader(FlowLoading):
    """
    solid-description: Loads and validates a flow definition from a YAML file.
    solid-category: service
    """

    def __init__(
        self,
        file_loader: YamlConfigFileLoader,
        config_extractor: FlowConfigExtracting,
        uses_resolver: UsesResolving,
        graph_validator: FlowGraphValidating,
        step_builder: StepBuilding,
    ) -> None:
        self._file_loader = file_loader
        self._config_extractor = config_extractor
        self._uses_resolver = uses_resolver
        self._graph_validator = graph_validator
        self._step_builder = step_builder

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

        self._graph_validator.validate_raw(resolved_steps)
        steps = [self._step_builder.build(s) for s in resolved_steps]
        self._graph_validator.validate_for_each_references(steps)

        return FlowDef(name=name, max_turns=max_turns, steps=steps)