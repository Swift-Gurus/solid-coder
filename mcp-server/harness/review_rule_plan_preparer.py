"""Prepares durable effective rule planning before review execution."""

from pathlib import Path

from harness.effective_rule_plan import EffectiveRulePlan
from harness.effective_rule_plan_building import EffectiveRulePlanBuilding
from harness.review_plan_artifact_persisting import ReviewPlanArtifactPersisting
from harness.review_policy_loading import ReviewPolicyLoading
from harness.workflow_catalog_resolving import WorkflowCatalogResolving


"""
solid-name: ReviewRulePlanPreparer
solid-category: service
solid-spec: [SPEC-039]
solid-description: Coordinates policy loading, catalog planning, and mandatory audit persistence before review execution.
"""
class ReviewRulePlanPreparer:

    def __init__(
        self,
        policy_loader: ReviewPolicyLoading,
        catalog_resolver: WorkflowCatalogResolving,
        plan_builder: EffectiveRulePlanBuilding,
        artifact_persister: ReviewPlanArtifactPersisting,
    ) -> None:
        self._policy_loader = policy_loader
        self._catalog_resolver = catalog_resolver
        self._plan_builder = plan_builder
        self._artifact_persister = artifact_persister

    def prepare(
        self,
        run_dir: Path,
        workflow_roots: list[Path],
    ) -> EffectiveRulePlan:
        policy_resolution = self._policy_loader.load()
        catalog = self._catalog_resolver.catalog(
            [str(workflow_root) for workflow_root in workflow_roots]
        )
        plan = self._plan_builder.build(catalog, policy_resolution)
        self._artifact_persister.persist(run_dir, plan, policy_resolution)
        return plan
