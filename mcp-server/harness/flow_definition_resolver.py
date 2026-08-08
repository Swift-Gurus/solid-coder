"""Resolves a raw workflow document and all composition resources."""

from pathlib import Path

from harness.flow_config_extractor import FlowConfigExtracting
from harness.flow_def import FlowDef
from harness.include_resolving import IncludeResolving
from harness.output_schema_prompt_annotating import OutputSchemaPromptAnnotating
from harness.output_schema_resolving import OutputSchemaResolving
from harness.prompt_content_resolving import PromptContentResolving
from harness.step_source_annotating import StepSourceAnnotating
from harness.uses_resolving import UsesResolving


"""
solid-name: FlowDefinitionResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Runs the ordered workflow composition and resource-resolution pipeline with source provenance.
"""
class FlowDefinitionResolver:

    def __init__(
        self,
        config_extractor: FlowConfigExtracting,
        source_annotator: StepSourceAnnotating,
        uses_resolver: UsesResolving,
        include_resolver: IncludeResolving,
        prompt_resolver: PromptContentResolving,
        schema_resolver: OutputSchemaResolving,
        prompt_annotator: OutputSchemaPromptAnnotating,
    ) -> None:
        self._config_extractor = config_extractor
        self._source_annotator = source_annotator
        self._uses_resolver = uses_resolver
        self._include_resolver = include_resolver
        self._prompt_resolver = prompt_resolver
        self._schema_resolver = schema_resolver
        self._prompt_annotator = prompt_annotator

    def resolve(self, raw: dict, path: str, search_paths: list[str]) -> FlowDef:
        source_path = str(Path(path).resolve())
        workflow_id = raw.get("id") or Path(source_path).stem
        declared_steps = self._source_annotator.annotate(
            self._config_extractor.extract_steps(raw),
            source_path,
        )
        top_level_steps = self._resolve_uses(declared_steps, path, search_paths)
        top_level_step_ids = {step["id"] for step in top_level_steps if "id" in step}
        inclusion = self._include_resolver.resolve(
            top_level_steps,
            path,
            search_paths,
            root_workflow_id=workflow_id,
        )
        included_steps = self._resolve_uses(inclusion.steps, path, search_paths)
        prompt_steps = [self._prompt_resolver.resolve(step, path) for step in included_steps]
        schema_steps = [self._schema_resolver.resolve(step, path) for step in prompt_steps]
        resolved_steps = [self._prompt_annotator.annotate(step) for step in schema_steps]

        return FlowDef(
            id=workflow_id,
            name=self._config_extractor.extract_name(raw),
            max_turns=self._config_extractor.extract_max_turns(raw),
            steps=[],
            raw_steps=resolved_steps,
            top_level_step_ids=top_level_step_ids,
            alias_groups=inclusion.alias_groups,
            include_chain=inclusion.include_chain,
            source_path=source_path,
            sources=list(dict.fromkeys([source_path, *inclusion.sources])),
            workflow_ids=list(dict.fromkeys([workflow_id, *inclusion.workflow_ids])),
        )

    def _resolve_uses(self, steps: list[dict], path: str, search_paths: list[str]) -> list[dict]:
        return [self._uses_resolver.resolve(step, path, search_paths) for step in steps]
