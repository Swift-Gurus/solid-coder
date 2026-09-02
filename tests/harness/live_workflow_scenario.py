"""Defines one workflow invocation used by the shared live E2E contract."""

from dataclasses import dataclass

from pydantic import BaseModel

from live_session_artifact_scope import LiveSessionArtifactScope


"""
solid-name: LiveWorkflowScenario
solid-category: value
solid-description: Carries a workflow identity, typed parameters, and artifact ownership for one live E2E scenario.
"""
@dataclass(frozen=True)
class LiveWorkflowScenario:
    workflow_id: str
    parameters: BaseModel
    artifact_scope: LiveSessionArtifactScope
    model_context: str = ""
