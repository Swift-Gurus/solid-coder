"""Assembles a fully configured flow execution engine."""

from __future__ import annotations

from typing import Optional

from harness.agent_step_shape_validator import AgentStepShapeValidator
from harness.authored_workflow_outputs import AuthoredWorkflowOutputs
from harness.batch_step_presentation_builder import BatchStepPresentationBuilder
from harness.batch_step_presentation_resolver import BatchStepPresentationResolver
from harness.builtin_attribute_reader import BuiltinAttributeReader
from harness.command_allowlist_resolver import CommandAllowlistResolver
from harness.command_allowlist_resolving import CommandAllowlistResolving
from harness.command_allowlist_validator import CommandAllowlistValidator
from harness.command_step_shape_validator import CommandStepShapeValidator
from harness.command_step_value_validator import CommandStepValueValidator
from harness.comparison_condition_parser import ComparisonConditionParser
from harness.comparison_operation_parser import ComparisonOperationParser
from harness.composition_condition_parser import CompositionConditionParser
from harness.condition_comparator import ConditionComparator
from harness.condition_declaration_evaluator import ConditionDeclarationEvaluator
from harness.condition_evaluator import ConditionEvaluator
from harness.condition_parser import ConditionParser
from harness.condition_reference_resolver import ConditionReferenceResolver
from harness.condition_value_matcher import ConditionValueMatcher
from harness.conditional_step_instance_builder import ConditionalStepInstanceBuilder
from harness.dag_runner import DAGRunner
from harness.data_output_validator import DataOutputValidator
from harness.delegate_step_shape_validator import DelegateStepShapeValidator
from harness.directed_graph_factory import DirectedGraphFactory
from harness.dynamic_workflow_steps_resolver import DynamicWorkflowStepsResolver
from harness.dynamic_include_group_hierarchy_resolver import (
    DynamicIncludeGroupHierarchyResolver,
)
from harness.dynamic_workflow_materialization_builder import (
    DynamicWorkflowMaterializationBuilder,
)
from harness.dynamic_include_alias_groups_assembler import (
    DynamicIncludeAliasGroupsAssembler,
)
from harness.dynamic_include_alias_groups_selector import (
    DynamicIncludeAliasGroupsSelector,
)
from harness.event_appender import EventAppender, EventSerializer, POSIXFileAppender
from harness.event_replayer import EventParser, EventReplayer
from harness.expression_evaluating import ExpressionEvaluating
from harness.expression_resolver import ExpressionResolver
from harness.file_output_validator import FileOutputValidator
from harness.filtered_expression_evaluator import FilteredExpressionEvaluator
from harness.filter_resolver import FilterResolver
from harness.flow_config_extractor import FlowConfigExtractor
from harness.flow_definition_assembler import FlowDefinitionAssembler
from harness.flow_definition_resolver import FlowDefinitionResolver
from harness.flow_definition_validator import FlowDefinitionValidator
from harness.flow_engine_assembly import FlowEngineAssembly
from harness.flow_loader import FlowLoader
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.for_each_collection_validator import ForEachCollectionValidator
from harness.for_each_declaration_parser import ForEachDeclarationParser
from harness.for_each_items_resolver import ForEachItemsResolver
from harness.for_each_reference_parser import ForEachReferenceParser
from harness.for_each_reference_validator import ForEachReferenceValidator
from harness.for_each_source_identity_resolver import ForEachSourceIdentityResolver
from harness.group_dependency_expander import GroupDependencyExpander
from harness.include_alias_collision_validator import IncludeAliasCollisionValidator
from harness.include_alias_group_entry_parser import IncludeAliasGroupEntryParser
from harness.include_alias_group_for_each_parser import (
    IncludeAliasGroupForEachParser,
)
from harness.include_alias_group_finder import IncludeAliasGroupFinder
from harness.include_alias_group_snapshot_parser import IncludeAliasGroupSnapshotParser
from harness.include_cycle_validator import IncludeCycleValidator
from harness.include_group_membership_resolver import IncludeGroupMembershipResolver
from harness.include_group_dynamic_checker import IncludeGroupDynamicChecker
from harness.include_group_opacity_validator import IncludeGroupOpacityValidator
from harness.include_group_readiness_checker import IncludeGroupReadinessChecker
from harness.include_group_templates_selector import IncludeGroupTemplatesSelector
from harness.include_alias_group_for_each_normalizer import (
    IncludeAliasGroupForEachNormalizer,
)
from harness.include_alias_group_input_bindings_normalizer import (
    IncludeAliasGroupInputBindingsNormalizer,
)
from harness.include_resolver_factory import IncludeResolverFactory
from harness.include_structure_validator import IncludeStructureValidator
from harness.interpolation_error_factory import InterpolationErrorFactory
from harness.interpolator import Interpolator
from harness.hierarchical_dynamic_workflow_materializer import (
    HierarchicalDynamicWorkflowMaterializer,
)
from harness.incoming_edge_checker import IncomingEdgeChecker
from harness.included_workflow_dependencies_resolver import (
    IncludedWorkflowDependenciesResolver,
)
from harness.included_workflow_step_identity_resolver import (
    IncludedWorkflowStepIdentityResolver,
)
from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.included_workflow_steps_resolver import IncludedWorkflowStepsResolver
from harness.json_loading import JsonLoader
from harness.json_schema_validating import JsonSchemaValidator
from harness.kahn_cycle_detector import KahnCycleDetector
from harness.metric_declaration import MetricDeclaration
from harness.metric_declaration_decoder import MetricDeclarationDecoder
from harness.materialized_workflow_instances_collector import (
    MaterializedWorkflowInstancesCollector,
)
from harness.nested_component_accessor import NestedComponentAccessor
from harness.nested_path_resolver import NestedPathResolver
from harness.logical_operation_name_validator import LogicalOperationNameValidator
from harness.operation_inputs_resolver import OperationInputsResolver
from harness.operation_registration_resolving import OperationRegistrationResolving
from harness.operation_registry import OperationRegistry
from harness.operation_step_contract_resolver import OperationStepContractResolver
from harness.operation_step_shape_validator import OperationStepShapeValidator
from harness.output_schema_declaration_validator import OutputSchemaDeclarationValidator
from harness.output_collection_resolver import OutputCollectionResolver
from harness.output_schema_file_loader import OutputSchemaFileLoader
from harness.output_schema_description_collector import OutputSchemaDescriptionCollector
from harness.output_schema_prompt_annotator import OutputSchemaPromptAnnotator
from harness.output_schema_reference_resolver import OutputSchemaReferenceResolver
from harness.output_schema_resolver import OutputSchemaResolver
from harness.output_validating import OutputValidating
from harness.owned_include_dependencies_rebaser import (
    OwnedIncludeDependenciesRebaser,
)
from harness.path_builder import PathBuilder
from harness.path_checking import PathChecker
from harness.prompt_content_resolver import PromptContentResolver
from harness.prompt_file_loader import PromptFileLoader
from harness.prompt_file_path_resolver import PromptFilePathResolver
from harness.registered_template_value_renderer import RegisteredTemplateValueRenderer
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.nested_include_group_runtime_rebaser import (
    NestedIncludeGroupRuntimeRebaser,
)
from harness.recursive_dynamic_include_group_expander import (
    RecursiveDynamicIncludeGroupExpander,
)
from harness.recursive_dynamic_include_group_materializer import (
    RecursiveDynamicIncludeGroupMaterializer,
)
from harness.runtime_include_identity_qualifier import RuntimeIncludeIdentityQualifier
from harness.pydantic_operation_output_specs_resolver import (
    PydanticOperationOutputSpecsResolver,
)
from harness.resolved_output_schema_applier import ResolvedOutputSchemaApplier
from harness.resolved_outputs_applier import ResolvedOutputsApplier
from harness.resolved_prompt_applier import ResolvedPromptApplier
from harness.resolved_script_file_applier import ResolvedScriptFileApplier
from harness.resolved_step_resources_applier import ResolvedStepResourcesApplier
from harness.resolved_step_resources_factory import ResolvedStepResourcesFactory
from harness.run_state_reconstructor_factory import make_run_state_reconstructor
from harness.rule_declaration import RuleDeclaration
from harness.rule_additional_info_output_provider import (
    RuleAdditionalInfoOutputProvider,
)
from harness.rule_step_contract_resolver import RuleStepContractResolver
from harness.rule_validating_flow_definition_validator import (
    RuleValidatingFlowDefinitionValidator,
)
from harness.rule_workflow_validator import RuleWorkflowValidator
from harness.rule_workflow_validation_plan_validator import (
    RuleWorkflowValidationPlanValidator,
)
from harness.rule_workflow_validation_planner import (
    RuleWorkflowValidationPlanner,
)
from harness.rule_workflow_validation_scope_validator import (
    RuleWorkflowValidationScopeValidator,
)
from harness.rule_match_validator import RuleMatchValidator
from harness.review_policy_loading import ReviewPolicyLoading
from harness.schema_resolving import SchemaResolver
from harness.schema_validator import SchemaValidator
from harness.scalar_template_value_renderer import ScalarTemplateValueRenderer
from harness.script_file_resolver import ScriptFileResolver
from harness.script_step_shape_validator import ScriptStepShapeValidator
from harness.script_step_value_validator import ScriptStepValueValidator
from harness.step_builder import StepBuilder
from harness.step_condition_applier import StepConditionApplier
from harness.step_collection_uses_resolver import StepCollectionUsesResolver
from harness.step_declaring_file_resolver import StepDeclaringFileResolver
from harness.step_declaration_factory import StepDeclarationFactory
from harness.step_dependency_checker import StepDependencyChecker
from harness.step_dependency_reachability_checker import StepDependencyReachabilityChecker
from harness.step_dependency_graph_factory import StepDependencyGraphFactory
from harness.step_executable_resolver import StepExecutableResolver
from harness.step_field_validator_registration import StepFieldValidatorRegistration
from harness.step_graph_validator import StepGraphValidator
from harness.step_identity_resolver import StepIdentityResolver
from harness.step_instance_expander import StepInstanceExpander
from harness.step_instance_builder import StepInstanceBuilder
from harness.step_for_each_declaration_resolver import (
    StepForEachDeclarationResolver,
)
from harness.step_prompt_augmenter import StepPromptAugmenter
from harness.step_readiness_checker import StepReadinessChecker
from harness.step_shape_validator import StepShapeValidator
from harness.step_source_collector import StepSourceCollector
from harness.step_source_annotator import StepSourceAnnotator
from harness.step_status_checker import StepStatusChecker
from harness.step_output_expression_resolver import StepOutputExpressionResolver
from harness.step_output_reference_parser import StepOutputReferenceParser
from harness.step_output_reference_resolver import StepOutputReferenceResolver
from harness.step_output_workflow_input_binding_normalizer import (
    StepOutputWorkflowInputBindingNormalizer,
)
from harness.strict_collection_value_matcher import StrictCollectionValueMatcher
from harness.strict_value_comparator import StrictValueComparator
from harness.uses_resolver import UsesResolver
from harness.unique_step_identity_validator import UniqueStepIdentityValidator
from harness.unique_string_validator import UniqueStringValidator
from harness.workflow_catalog_resolving import WorkflowCatalogResolving
from harness.workflow_alias_results import WorkflowAliasResults
from harness.workflow_catalog_factory import WorkflowCatalogFactory
from harness.workflow_config_resource_loader import WorkflowConfigResourceLoader
from harness.workflow_include_runtime_parser import WorkflowIncludeRuntimeParser
from harness.workflow_input_binding_snapshot_parser import (
    WorkflowInputBindingSnapshotParser,
)
from harness.workflow_input_bindings_resolver import WorkflowInputBindingsResolver
from harness.workflow_expression_parser import WorkflowExpressionParser
from harness.workflow_output_declaration_parser import WorkflowOutputDeclarationParser
from harness.workflow_output_declaration_resolver import WorkflowOutputDeclarationResolver
from harness.workflow_alias_results_template_value_renderer import (
    WorkflowAliasResultsTemplateValueRenderer,
)
from harness.workflow_result_envelope_serializer import WorkflowResultEnvelopeSerializer
from harness.template_value_renderer_registration import TemplateValueRendererRegistration
from harness.workflow_package_root_locator import WorkflowPackageRootLocator
from harness.workflow_resource_directory import WorkflowResourceDirectory
from harness.workflow_resource_path_classifier import WorkflowResourcePathClassifier
from harness.workflow_resource_path_resolver import WorkflowResourcePathResolver
from harness.workflow_resource_reference_factory import WorkflowResourceReferenceFactory
from harness.workflow_step_context_resolver import WorkflowStepContextResolver
from harness.workflow_results_visibility_selector import (
    WorkflowResultsVisibilitySelector,
)
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader
from json_serializer import JsonSerializer
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: FlowEngineAssemblyFactory
solid-category: service
solid-spec: [SPEC-030, SPEC-035]
solid-description: Provides a ready-to-use flow execution engine with workflow loading, validation, orchestration, and event services.
"""
class FlowEngineAssemblyFactory:
    def build(
        self,
        command_allowlist_resolver: Optional[CommandAllowlistResolving] = None,
        workflow_catalog_resolver: Optional[WorkflowCatalogResolving] = None,
        operation_registry: Optional[OperationRegistrationResolving] = None,
        review_policy_loader: Optional[ReviewPolicyLoading] = None,
    ) -> FlowEngineAssembly:
        allowlist_resolver = command_allowlist_resolver or CommandAllowlistResolver()
        catalog_resolver = workflow_catalog_resolver or WorkflowCatalogFactory().make()
        yaml_file_loader = YamlConfigFileLoader(loader=PyYamlLoader())
        json_file_loader = YamlConfigFileLoader(loader=JsonLoader())
        path_builder = PathBuilder()
        error_factory = FlowValidationErrorFactory()
        registered_operations = operation_registry or OperationRegistry(
            registrations=[],
            name_validator=LogicalOperationNameValidator(),
            error_factory=error_factory,
        )
        package_root_locator = WorkflowPackageRootLocator()
        resource_path_classifier = WorkflowResourcePathClassifier()
        prompt_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.PROMPTS,
        )
        schema_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.SCHEMAS,
        )
        steps_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.STEPS,
        )
        subflow_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.SUBFLOWS,
        )
        script_reference_factory = WorkflowResourceReferenceFactory(
            resource_path_classifier,
            WorkflowResourceDirectory.SCRIPTS,
        )
        resource_path_resolver = WorkflowResourcePathResolver(
            package_root_locator=package_root_locator,
            error_factory=error_factory,
        )
        json_resource_loader = WorkflowConfigResourceLoader(
            file_loader=json_file_loader,
            path_resolver=resource_path_resolver,
        )
        yaml_resource_loader = WorkflowConfigResourceLoader(
            file_loader=yaml_file_loader,
            path_resolver=resource_path_resolver,
        )
        source_annotator = StepSourceAnnotator()
        workflow_expression_parser = WorkflowExpressionParser()
        condition_parser = ConditionParser(
            composition_parser=CompositionConditionParser(),
            comparison_parser=ComparisonConditionParser(
                expression_parser=workflow_expression_parser,
                operation_parser=ComparisonOperationParser(error_factory),
            ),
        )
        interpolation_error_factory = InterpolationErrorFactory()
        step_output_reference_parser = StepOutputReferenceParser()
        output_schema_file_loader = OutputSchemaFileLoader(
            resource_loader=json_resource_loader,
            reference_factory=schema_reference_factory,
            error_factory=error_factory,
        )
        workflow_output_parser = WorkflowOutputDeclarationParser(
            decoder=PydanticModelDecoder(
                model_type=AuthoredWorkflowOutputs,
            ),
            declaration_resolver=WorkflowOutputDeclarationResolver(
                expression_parser=workflow_expression_parser,
                reference_parser=step_output_reference_parser,
                schema_loader=output_schema_file_loader,
            ),
        )
        for_each_reference_parser = ForEachReferenceParser(
            expression_parser=workflow_expression_parser,
            reference_parser=step_output_reference_parser,
        )
        for_each_declaration_parser = ForEachDeclarationParser(
            reference_parser=for_each_reference_parser,
            expression_parser=workflow_expression_parser,
        )
        include_runtime_parser = WorkflowIncludeRuntimeParser(
            condition_parser=condition_parser,
            for_each_parser=for_each_declaration_parser,
            expression_parser=workflow_expression_parser,
            error_factory=error_factory,
        )
        step_output_reference_resolver = StepOutputReferenceResolver[object](
            interpolation_error_factory
        )
        nested_value_resolver = NestedPathResolver(
            component_accessor=NestedComponentAccessor(
                attribute_reader=BuiltinAttributeReader()
            ),
            error_factory=interpolation_error_factory,
        )
        unfiltered_expression_resolver = ExpressionResolver(
            step_output_resolver=StepOutputExpressionResolver(
                reference_parser=step_output_reference_parser,
                reference_resolver=step_output_reference_resolver,
                error_factory=interpolation_error_factory,
            ),
            nested_value_resolver=nested_value_resolver,
            error_factory=interpolation_error_factory,
        )
        expression_resolver: ExpressionEvaluating = FilteredExpressionEvaluator(
            expression_evaluator=unfiltered_expression_resolver,
            filter_resolver=FilterResolver(),
        )
        interpolator = Interpolator(
            evaluator=expression_resolver,
            value_renderer=RegisteredTemplateValueRenderer(
                registrations=[
                    TemplateValueRendererRegistration(
                        value_type=WorkflowAliasResults,
                        renderer=WorkflowAliasResultsTemplateValueRenderer(
                            envelope_serializer=WorkflowResultEnvelopeSerializer(),
                            json_serializer=JsonSerializer(),
                        ),
                    ),
                ],
                default_renderer=ScalarTemplateValueRenderer(),
            ),
        )
        graph_factory = DirectedGraphFactory()
        cycle_detector = KahnCycleDetector(IncomingEdgeChecker())
        step_identity_resolver = StepIdentityResolver(error_factory)
        dependency_validator = StepGraphValidator(
            identity_validator=UniqueStepIdentityValidator(
                step_identity_resolver,
                UniqueStringValidator(error_factory),
            ),
            graph_factory=StepDependencyGraphFactory(
                identity_resolver=step_identity_resolver,
                graph_factory=graph_factory,
                error_factory=error_factory,
            ),
            cycle_detector=cycle_detector,
            error_factory=error_factory,
        )
        include_structure_validator = IncludeStructureValidator(
            alias_collision_validator=IncludeAliasCollisionValidator(error_factory),
            group_opacity_validator=IncludeGroupOpacityValidator(
                membership_resolver=IncludeGroupMembershipResolver(),
                error_factory=error_factory,
            ),
            include_cycle_validator=IncludeCycleValidator(
                graph_factory=graph_factory,
                cycle_detector=cycle_detector,
                error_factory=error_factory,
            ),
        )

        uses_resolver = UsesResolver(
                resource_loader=yaml_resource_loader,
                reference_factory=steps_reference_factory,
                package_root_locator=package_root_locator,
                path_builder=path_builder,
                error_factory=error_factory,
            )
        include_resolver = IncludeResolverFactory(
            file_loader=yaml_file_loader,
            resource_loader=yaml_resource_loader,
            catalog_resolver=catalog_resolver,
            source_annotator=source_annotator,
            runtime_parser=include_runtime_parser,
            path_builder=path_builder,
            subflow_reference_factory=subflow_reference_factory,
            output_parser=workflow_output_parser,
            error_factory=error_factory,
            review_policy_loader=review_policy_loader,
        ).make()
        step_resources_factory = ResolvedStepResourcesFactory()
        step_resources_applier = ResolvedStepResourcesApplier()
        prompt_resolver = PromptContentResolver(
            path_resolver=PromptFilePathResolver(
                path_builder=path_builder,
                resource_path_resolver=resource_path_resolver,
                reference_factory=prompt_reference_factory,
            ),
            prompt_loader=PromptFileLoader(
                reader=PlainTextFileReader(),
                error_factory=error_factory,
            ),
            prompt_applier=ResolvedPromptApplier(
                resources_factory=step_resources_factory,
                resources_applier=step_resources_applier,
            ),
        )
        schema_resolver = OutputSchemaResolver(
            declaring_file_resolver=StepDeclaringFileResolver(path_builder),
            output_collection_resolver=OutputCollectionResolver(
                schema_reference_resolver=OutputSchemaReferenceResolver(
                    declaration_validator=OutputSchemaDeclarationValidator(error_factory),
                    schema_loader=output_schema_file_loader,
                    schema_applier=ResolvedOutputSchemaApplier(),
                    identity_resolver=step_identity_resolver,
                )
            ),
            outputs_applier=ResolvedOutputsApplier(
                resources_factory=step_resources_factory,
                resources_applier=step_resources_applier,
            ),
        )
        dynamic_group_checker = IncludeGroupDynamicChecker()
        group_dependency_expander = GroupDependencyExpander(
            IncludeAliasGroupFinder()
        )
        flow_loader = FlowLoader(
            file_loader=yaml_file_loader,
            definition_resolver=FlowDefinitionResolver(
                config_extractor=FlowConfigExtractor(),
                condition_parser=condition_parser,
                path_builder=path_builder,
                source_annotator=source_annotator,
                source_collector=StepSourceCollector(),
                uses_resolver=StepCollectionUsesResolver(uses_resolver),
                include_resolver=include_resolver,
                alias_group_snapshot_parser=IncludeAliasGroupSnapshotParser(
                    group_parser=IncludeAliasGroupEntryParser(
                        binding_parser=WorkflowInputBindingSnapshotParser(
                            workflow_expression_parser
                        ),
                        condition_parser=condition_parser,
                        for_each_parser=IncludeAliasGroupForEachParser(
                            for_each_declaration_parser
                        ),
                        rule_workflow_decoder=PydanticModelDecoder(
                            model_type=IncludedRuleWorkflow,
                        ),
                        output_parser=workflow_output_parser,
                        error_factory=error_factory,
                    )
                ),
                script_file_resolver=ScriptFileResolver(
                    declaring_file_resolver=StepDeclaringFileResolver(path_builder),
                    resource_path_resolver=resource_path_resolver,
                    reference_factory=script_reference_factory,
                    script_file_applier=ResolvedScriptFileApplier(
                        resources_factory=step_resources_factory,
                        resources_applier=step_resources_applier,
                    ),
                ),
                prompt_resolver=prompt_resolver,
                schema_resolver=schema_resolver,
                prompt_annotator=OutputSchemaPromptAnnotator(
                    description_collector=OutputSchemaDescriptionCollector(
                        JsonSerializer()
                    ),
                    prompt_augmenter=StepPromptAugmenter(),
                ),
                step_mapper=StepDeclarationFactory(
                    condition_parser=condition_parser,
                    for_each_parser=for_each_declaration_parser,
                    rule_step_contract_resolver=RuleStepContractResolver(
                        metric_decoder=MetricDeclarationDecoder(
                            PydanticModelDecoder(
                                model_type=MetricDeclaration,
                            )
                        ),
                        additional_info_output=RuleAdditionalInfoOutputProvider(),
                        error_factory=error_factory,
                    ),
                    operation_step_contract_resolver=OperationStepContractResolver(
                        registry=registered_operations,
                        expression_parser=workflow_expression_parser,
                        output_specs_resolver=PydanticOperationOutputSpecsResolver(
                            error_factory
                        ),
                        error_factory=error_factory,
                    ),
                ),
                rule_decoder=PydanticModelDecoder(
                    model_type=RuleDeclaration,
                ),
            ),
            definition_validator=RuleValidatingFlowDefinitionValidator(
                delegate=FlowDefinitionValidator(
                    step_shape_validator=StepShapeValidator(
                        registrations=[
                            StepFieldValidatorRegistration(
                                "agent",
                                AgentStepShapeValidator(error_factory),
                            ),
                            StepFieldValidatorRegistration(
                                "script",
                                ScriptStepShapeValidator(
                                    ScriptStepValueValidator(error_factory),
                                    error_factory,
                                ),
                            ),
                            StepFieldValidatorRegistration(
                                "command",
                                CommandStepShapeValidator(
                                    CommandStepValueValidator(error_factory),
                                    error_factory,
                                ),
                            ),
                            StepFieldValidatorRegistration(
                                "delegate",
                                DelegateStepShapeValidator(error_factory),
                            ),
                            StepFieldValidatorRegistration(
                                "operation",
                                OperationStepShapeValidator(error_factory),
                            ),
                        ],
                        default=AgentStepShapeValidator(error_factory),
                    ),
                    command_allowlist_resolver=allowlist_resolver,
                    command_allowlist_validator=CommandAllowlistValidator(
                        executable_resolver=StepExecutableResolver(),
                        error_factory=error_factory,
                    ),
                    dependency_validator=dependency_validator,
                    include_validator=include_structure_validator,
                    for_each_validator=ForEachCollectionValidator(
                        target_validator=ForEachReferenceValidator(
                            reachability_checker=StepDependencyReachabilityChecker(),
                        ),
                        source_identity_resolver=ForEachSourceIdentityResolver(),
                    ),
                ),
                rule_validator=RuleWorkflowValidator(
                    planner=RuleWorkflowValidationPlanner(),
                    plan_validator=RuleWorkflowValidationPlanValidator(
                        scope_validator=RuleWorkflowValidationScopeValidator(
                            match_validator=RuleMatchValidator(error_factory),
                            identity_validator=UniqueStringValidator(error_factory),
                            error_factory=error_factory,
                        ),
                        error_factory=error_factory,
                    ),
                ),
            ),
            definition_assembler=FlowDefinitionAssembler(
                group_dependency_expander=group_dependency_expander,
                dynamic_group_checker=dynamic_group_checker,
                dynamic_groups=DynamicIncludeAliasGroupsAssembler(
                    selector=DynamicIncludeAliasGroupsSelector(
                        dynamic_group_checker
                    ),
                    for_each=IncludeAliasGroupForEachNormalizer(
                        ForEachSourceIdentityResolver()
                    ),
                    input_bindings=IncludeAliasGroupInputBindingsNormalizer(
                        binding=StepOutputWorkflowInputBindingNormalizer(
                            reference_parser=step_output_reference_parser,
                            source_identity=ForEachSourceIdentityResolver(),
                        )
                    ),
                ),
                step_builder=StepBuilder(),
            ),
            error_factory=error_factory,
        )

        event_appender = EventAppender(
            serializer=EventSerializer(),
            file_appender=POSIXFileAppender(),
        )
        event_replayer = EventReplayer(
            parser=EventParser(),
            reconstructor=make_run_state_reconstructor(),
        )
        validators: dict[str, OutputValidating] = {
            "file": FileOutputValidator(path_checker=PathChecker()),
            "data": DataOutputValidator(
                schema_resolver=SchemaResolver(),
                json_schema=JsonSchemaValidator(),
            ),
        }
        strict_value_comparator = StrictValueComparator()
        condition_evaluator = ConditionEvaluator(
            declaration_evaluator=ConditionDeclarationEvaluator(),
            comparison_runtime=ConditionComparator(
                reference_resolver=ConditionReferenceResolver(
                    expression_evaluator=unfiltered_expression_resolver,
                ),
                value_matcher=ConditionValueMatcher(
                    comparator=strict_value_comparator,
                    collection_matcher=StrictCollectionValueMatcher(
                        strict_value_comparator
                    ),
                ),
            ),
        )
        dependency_checker = StepDependencyChecker()
        items_resolver = ForEachItemsResolver(
            reference_resolver=StepOutputReferenceResolver[list[object]](
                interpolation_error_factory
            ),
        )
        input_bindings_resolver = WorkflowInputBindingsResolver(
            evaluator=expression_resolver,
        )
        workflow_step_context_resolver = WorkflowStepContextResolver(
            results_selector=WorkflowResultsVisibilitySelector()
        )
        included_step_identity_resolver = IncludedWorkflowStepIdentityResolver()
        runtime_identity_qualifier = RuntimeIncludeIdentityQualifier(
            included_step_identity_resolver
        )
        owned_dependency_rebaser = OwnedIncludeDependenciesRebaser(
            runtime_identity_qualifier
        )
        dynamic_step_resolver = DynamicWorkflowStepsResolver(
            materializer=HierarchicalDynamicWorkflowMaterializer(
                hierarchy_resolver=DynamicIncludeGroupHierarchyResolver(
                    dynamic_group_checker
                ),
                group_expander=RecursiveDynamicIncludeGroupExpander(
                    group_materializer=RecursiveDynamicIncludeGroupMaterializer(
                        readiness_checker=IncludeGroupReadinessChecker(
                            dependency_checker
                        ),
                        items_resolver=items_resolver,
                        included_steps_resolver=IncludedWorkflowStepsResolver(
                            input_resolver=input_bindings_resolver,
                            identity_resolver=included_step_identity_resolver,
                            dependency_resolver=IncludedWorkflowDependenciesResolver(),
                        ),
                        runtime_rebaser=NestedIncludeGroupRuntimeRebaser(
                            identity=runtime_identity_qualifier,
                            dependency_rebaser=owned_dependency_rebaser,
                        ),
                        context_resolver=workflow_step_context_resolver,
                        template_selector=IncludeGroupTemplatesSelector(),
                        instance_collector=MaterializedWorkflowInstancesCollector(),
                        dependency_rebaser=owned_dependency_rebaser,
                    )
                ),
                result_builder=DynamicWorkflowMaterializationBuilder(),
            ),
            group_dependency_expander=group_dependency_expander,
        )
        return FlowEngineAssembly(
            flow_loader=flow_loader,
            event_appender=event_appender,
            event_replayer=event_replayer,
            dynamic_step_resolver=dynamic_step_resolver,
            dag_runner=DAGRunner(
                readiness_checker=StepReadinessChecker(
                    status_checker=StepStatusChecker(),
                    dependency_checker=dependency_checker,
                ),
                instance_expander=StepInstanceExpander(
                    items_resolver=items_resolver,
                    context_resolver=workflow_step_context_resolver,
                    instance_builder=ConditionalStepInstanceBuilder(
                        delegate=StepInstanceBuilder(
                            renderer=interpolator,
                            context_resolver=workflow_step_context_resolver,
                            operation_inputs_resolver=OperationInputsResolver(
                                input_bindings_resolver
                            ),
                            batch_presentation_resolver=(
                                BatchStepPresentationResolver(
                                    declaration_resolver=(
                                        StepForEachDeclarationResolver()
                                    ),
                                    presentation_builder=(
                                        BatchStepPresentationBuilder(
                                            expression_resolver
                                        )
                                    ),
                                )
                            ),
                        ),
                        condition_applier=StepConditionApplier(
                            condition_evaluator,
                            workflow_step_context_resolver,
                        ),
                    ),
                ),
            ),
            condition_evaluator=condition_evaluator,
            interpolator=interpolator,
            schema_validator=SchemaValidator(validators=validators),
        )
