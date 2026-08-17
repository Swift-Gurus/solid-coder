"""Assembles production review-rule policy planning and audit persistence."""

from pathlib import Path
from typing import Callable

from harness.effective_rule_plan_builder import EffectiveRulePlanBuilder
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.pydantic_model_decoder import PydanticModelDecoder
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
from harness.workflow_catalog_factory import make_workflow_catalog_builder
from scoring.yaml_loader import PyYamlLoader


def make_review_rule_plan_preparer(
    project_directory: Callable[[], Path],
) -> ReviewRulePlanPreparer:
    error_factory = FlowValidationErrorFactory()
    content_hasher = Sha256ContentHasher()
    return ReviewRulePlanPreparer(
        policy_loader=ReviewPolicyLoader(
            project_directory=project_directory,
            yaml_loader=PyYamlLoader(),
            parser=ReviewPolicyParser(
                decoder=PydanticModelDecoder(
                    model_type=ReviewPolicy,
                    error_factory=error_factory,
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
        catalog_builder=make_workflow_catalog_builder(),
        plan_builder=EffectiveRulePlanBuilder(
            target_validator=ReviewPolicyTargetValidator(error_factory),
            entry_builder=RulePlanEntryBuilder(
                content_hasher=content_hasher,
                enablement_resolver=RuleEnablementResolver(),
                origin_resolver=RuleWorkflowOriginResolver(project_directory),
                error_factory=error_factory,
            ),
        ),
        artifact_persister=ReviewPlanArtifactPersister(),
    )
