"""Prepares durable effective rule planning before review execution."""

from pathlib import Path

from harness.effective_rule_plan import EffectiveRulePlan
from harness.effective_rule_plan_building import EffectiveRulePlanBuilding
from harness.review_plan_artifact_persisting import ReviewPlanArtifactPersisting
from harness.review_policy_loading import ReviewPolicyLoading
from harness.workflow_catalog_building import WorkflowCatalogBuilding


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
        catalog_builder: WorkflowCatalogBuilding,
        plan_builder: EffectiveRulePlanBuilding,
        artifact_persister: ReviewPlanArtifactPersisting,
    ) -> None:
        self._policy_loader = policy_loader
        self._catalog_builder = catalog_builder
        self._plan_builder = plan_builder
        self._artifact_persister = artifact_persister

    def prepare(
        self,
        run_dir: Path,
        workflow_roots: list[Path],
    ) -> EffectiveRulePlan:
        policy_resolution = self._policy_loader.load()
        catalog = self._catalog_builder.build(workflow_roots)
        plan = self._plan_builder.build(catalog, policy_resolution)
        self._artifact_persister.persist(run_dir, plan, policy_resolution)
        return plan
