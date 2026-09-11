"""Defines locked live SRP assertions for aggregate workflow execution."""

from __future__ import annotations

from live_session_artifact_scope import LiveSessionArtifactScope
from live_workflow_scenario import LiveWorkflowScenario
from srp_validation_e2e_live_base import SRPValidationE2ELiveBase


"""
solid-name: AggregateSRPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-045]
solid-description: Applies locked SRP expectations to the canonical rules running through aggregate execution.
"""
class AggregateSRPValidationE2ELiveBase(SRPValidationE2ELiveBase):
    __test__ = False
    REVIEW_WORKFLOW_ID = "solid-file-review-aggregate"

    @property
    def scenario(self) -> LiveWorkflowScenario:
        baseline = super().scenario
        return LiveWorkflowScenario(
            workflow_id=self.REVIEW_WORKFLOW_ID,
            parameters=baseline.parameters,
            artifact_scope=LiveSessionArtifactScope(
                domain="review",
                scenario="srp-aggregate",
            ),
            model_context=baseline.model_context,
        )
