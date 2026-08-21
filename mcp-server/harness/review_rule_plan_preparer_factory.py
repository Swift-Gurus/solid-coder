"""Assembles production review-rule policy planning and audit persistence."""

from pathlib import Path
from typing import Callable

from harness.effective_metric_plan_resolver import EffectiveMetricPlanResolver
from harness.effective_rule_plan_builder import EffectiveRulePlanBuilder
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.metric_override_applier import MetricOverrideApplier
from harness.ordered_string_collector import OrderedStringCollector
from harness.review_plan_artifact_persister import ReviewPlanArtifactPersister
from harness.review_policy import ReviewPolicy
from harness.review_policy_identity_validator import ReviewPolicyIdentityValidator
from harness.review_policy_loader import ReviewPolicyLoader
from harness.review_policy_parser import ReviewPolicyParser
from harness.review_policy_target_validator import ReviewPolicyTargetValidator
from harness.review_rule_plan_preparer import ReviewRulePlanPreparer
from harness.rule_enablement_resolver import RuleEnablementResolver
from harness.rule_plan_entry_builder import RulePlanEntryBuilder
from harness.rule_workflow_origin_resolver import RuleWorkflowOriginResolver
from harness.sha256_content_hasher import Sha256ContentHasher
from harness.unique_string_validator import UniqueStringValidator
from harness.workflow_catalog_factory import WorkflowCatalogFactory
from scoring.yaml_loader import PyYamlLoader


"""
solid-name: ReviewRulePlanPreparerFactory
solid-category: factory
solid-spec: [SPEC-039]
solid-description: Provides a production review rule plan preparer.
"""
class ReviewRulePlanPreparerFactory:

    def __init__(self, project_directory: Callable[[], Path]) -> None:
        self._project_directory = project_directory

    def make(self) -> ReviewRulePlanPreparer:
        error_factory = FlowValidationErrorFactory()
        content_hasher = Sha256ContentHasher()
        return ReviewRulePlanPreparer(
            policy_loader=ReviewPolicyLoader(
                project_directory=self._project_directory,
                yaml_loader=PyYamlLoader(),
                parser=ReviewPolicyParser(
                    decoder=PydanticModelDecoder(
                        model_type=ReviewPolicy,
                    ),
                    validators=[
                        ReviewPolicyIdentityValidator(
                            UniqueStringValidator(error_factory)
                        )
                    ],
                ),
                content_hasher=content_hasher,
                error_factory=error_factory,
            ),
            catalog_resolver=WorkflowCatalogFactory().make(),
            plan_builder=EffectiveRulePlanBuilder(
                target_validator=ReviewPolicyTargetValidator(error_factory),
                entry_builder=RulePlanEntryBuilder(
                    content_hasher=content_hasher,
                    enablement_resolver=RuleEnablementResolver(),
                    origin_resolver=RuleWorkflowOriginResolver(
                        self._project_directory
                    ),
                    metric_plan_resolver=EffectiveMetricPlanResolver(
                        override_applier=MetricOverrideApplier(),
                        error_factory=error_factory,
                    ),
                    error_factory=error_factory,
                ),
                flow_loader=FlowEngineAssemblyFactory().build().flow_loader,
                search_path_collector=OrderedStringCollector(),
            ),
            artifact_persister=ReviewPlanArtifactPersister(),
        )
