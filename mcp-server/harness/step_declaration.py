"""Defines one unvalidated workflow-step declaration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, ClassVar

from harness.co_located_metric_contract import CoLocatedMetricContract
from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.condition_declaration import ConditionDeclaration
from harness.for_each_declaration import ForEachDeclaration
from harness.metric_declaration import MetricDeclaration
from harness.operation_step import OperationStep
from harness.output_spec import OutputSpec
from harness.rule_assessment_declaration import RuleAssessmentDeclaration
from pydantic import AliasChoices, ConfigDict, Field

"""
solid-name: StepDeclaration
solid-category: model
solid-spec: [SPEC-027, SPEC-035, SPEC-037, SPEC-039]
solid-description: Represents an unvalidated workflow step for later validation.
"""


@dataclass(frozen=True)
class StepDeclaration:
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
    )

    id: str | None = None
    type: str = "agent"
    prompt: str | None = None
    authored_prompt: str | None = None
    depends_on: list[str] | None = None
    outputs: list[OutputSpec] = field(default_factory=list)
    for_each: ForEachDeclaration | None = None
    condition: ConditionDeclaration | None = None
    mode: str | None = None
    prompt_file: str | None = None
    command: str | list[str] | None = None
    script_file_reference: Annotated[
        str | None,
        Field(validation_alias=AliasChoices("script_file_reference", "file")),
    ] = None
    script_file: str | None = None
    executor: str | None = None
    args: list[str] | None = None
    timeout_seconds: int | None = None
    max_attempts: int = 3
    source_file: str | None = None
    metric: MetricDeclaration | None = None
    metric_calculation: CollectionMetricCalculation | None = None
    assessment: RuleAssessmentDeclaration | None = None
    operation: OperationStep | None = None
    co_located_metrics: list[CoLocatedMetricContract] = field(default_factory=list)
