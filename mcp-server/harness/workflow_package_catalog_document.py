"""Defines the typed package fields required by workflow catalog discovery."""

from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints

from harness.rule_declaration import RuleDeclaration
from harness.workflow_id import WorkflowId


"""
solid-name: WorkflowPackageCatalogDocument
solid-category: model
solid-spec: [SPEC-035, SPEC-039]
solid-description: Represents validated package identity, catalog eligibility, steps, and optional rule enrollment metadata.
"""
class WorkflowPackageCatalogDocument(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    id: WorkflowId
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    max_turns: Annotated[StrictInt, Field(ge=1)]
    steps: Annotated[list[object], Field(min_length=1)]
    rule: Optional[RuleDeclaration] = None
