"""Defines a named group of expanded workflow-step identifiers."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.condition_declaration import ConditionDeclaration
from harness.for_each_declaration import ForEachDeclaration
from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_output_declaration import WorkflowOutputDeclaration


"""
solid-name: IncludeAliasGroup
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Represents one workflow include alias and its expanded member-step identifiers.
"""
@dataclass(frozen=True)
class IncludeAliasGroup:
    alias: str
    member_ids: list[str]
    authored_alias: str = ""
    owner_alias: str | None = None
    runtime_owner_instance_id: str | None = None
    depends_on: list[str] = field(default_factory=list)
    for_each: ForEachDeclaration | None = None
    input_bindings: list[WorkflowInputBinding] = field(default_factory=list)
    condition: ConditionDeclaration | None = None
    rule_workflow: IncludedRuleWorkflow | None = None
    outputs: list[WorkflowOutputDeclaration] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.authored_alias:
            object.__setattr__(self, "authored_alias", self.alias)
