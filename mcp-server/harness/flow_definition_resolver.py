"""Resolves a raw workflow document and all composition resources."""

from harness.flow_config_extractor import FlowConfigExtracting
from harness.flow_def import FlowDef
from harness.include_resolving import IncludeResolving
from harness.output_schema_prompt_annotating import OutputSchemaPromptAnnotating
from harness.output_schema_resolving import OutputSchemaResolving
from harness.path_building import PathBuilding
from harness.prompt_content_resolving import PromptContentResolving
from harness.resolved_flow_definition_creating import ResolvedFlowDefinitionCreating
from harness.script_file_resolving import ScriptFileResolving
from harness.step_collection_uses_resolving import StepCollectionUsesResolving
from harness.step_declaration_mapping import StepDeclarationMapping
from harness.step_source_collecting import StepSourceCollecting
from harness.step_source_annotating import StepSourceAnnotating


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
        path_builder: PathBuilding,
        source_annotator: StepSourceAnnotating,
        source_collector: StepSourceCollecting,
        uses_resolver: StepCollectionUsesResolving,
        include_resolver: IncludeResolving,
        script_file_resolver: ScriptFileResolving,
        prompt_resolver: PromptContentResolving,
        schema_resolver: OutputSchemaResolving,
        prompt_annotator: OutputSchemaPromptAnnotating,
        step_mapper: StepDeclarationMapping,
        definition_factory: ResolvedFlowDefinitionCreating,
    ) -> None:
        self._config_extractor = config_extractor
        self._path_builder = path_builder
        self._source_annotator = source_annotator
        self._source_collector = source_collector
        self._uses_resolver = uses_resolver
        self._include_resolver = include_resolver
        self._script_file_resolver = script_file_resolver
        self._prompt_resolver = prompt_resolver
        self._schema_resolver = schema_resolver
        self._prompt_annotator = prompt_annotator
        self._step_mapper = step_mapper
        self._definition_factory = definition_factory

    def resolve(self, raw: dict, path: str, search_paths: list[str]) -> FlowDef:
        resolved_source_path = self._path_builder.build(path)
        source_path = str(resolved_source_path)
        workflow_id = raw.get("id") or resolved_source_path.stem
        declared_steps = self._source_annotator.annotate(
            self._config_extractor.extract_steps(raw),
            source_path,
        )
        top_level_steps = self._uses_resolver.resolve(declared_steps, path, search_paths)
        top_level_step_ids = {step["id"] for step in top_level_steps if "id" in step}
        inclusion = self._include_resolver.resolve(
            top_level_steps,
            path,
            search_paths,
            root_workflow_id=workflow_id,
        )
        included_steps = self._uses_resolver.resolve(inclusion.steps, path, search_paths)
        sources = self._source_collector.collect(
            included_steps,
            [source_path, *inclusion.sources],
        )
        mapped_steps = [self._step_mapper.map(step) for step in included_steps]
        script_steps = [
            self._script_file_resolver.resolve(step, path) for step in mapped_steps
        ]
        prompt_steps = [self._prompt_resolver.resolve(step, path) for step in script_steps]
        schema_steps = [self._schema_resolver.resolve(step, path) for step in prompt_steps]
        step_declarations = [
            self._prompt_annotator.annotate(step) for step in schema_steps
        ]

        return self._definition_factory.create(
            workflow_id=workflow_id,
            name=self._config_extractor.extract_name(raw),
            max_turns=self._config_extractor.extract_max_turns(raw),
            step_declarations=step_declarations,
            top_level_step_ids=top_level_step_ids,
            alias_groups=inclusion.alias_groups,
            include_chain=inclusion.include_chain,
            source_path=source_path,
            sources=sources,
            workflow_ids=[workflow_id, *inclusion.workflow_ids],
        )
