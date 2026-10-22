"""Validates complete model judgments against authoritative metadata targets."""

from findings.metric_additional_info import MetricAdditionalInfo
from harness.operation_handling import OperationHandling
from source.frontmatter.bind_frontmatter_descriptions_input import BindFrontmatterDescriptionsInput
from source.frontmatter.frontmatter_description_decisions import FrontmatterDescriptionDecisions
from source.frontmatter.source_description_classification import SourceDescriptionClassification
from validation.collection_identity_binder import CollectionIdentityBinding


"""
solid-name: BindFrontmatterDescriptionsOperation
solid-category: service
solid-spec: [SPEC-069]
solid-description: Enforces exact description identity coverage and preserves one evidenced validity decision per metadata block.
"""
class BindFrontmatterDescriptionsOperation(OperationHandling[BindFrontmatterDescriptionsInput, FrontmatterDescriptionDecisions]):
    def __init__(self, binding: CollectionIdentityBinding[SourceDescriptionClassification]) -> None:
        self._binding = binding

    def execute(self, operation_input: BindFrontmatterDescriptionsInput) -> FrontmatterDescriptionDecisions:
        classifications = iter(self._binding.bind(
            [entry.declaration_id for entry in operation_input.targets],
            [entry.declaration_id for entry in operation_input.classifications],
            operation_input.classifications,
            "description declaration",
        ))
        decisions: list[SourceDescriptionClassification] = []
        for entry in operation_input.entries:
            if not entry.has_frontmatter:
                continue
            if entry.bad_description:
                decisions.append(SourceDescriptionClassification(
                    declaration_id=entry.declaration.identity,
                    classification="INVALID_FORMAT",
                    additional_info=MetricAdditionalInfo(
                        reasoning="The description is absent or fails the required abstraction prefix.",
                        evidence=f"{entry.declaration.unit.name}, line {entry.declaration.unit.span.start}: solid-description={entry.metadata.description!r}",
                    ),
                ))
                continue
            decisions.append(next(classifications))
        return FrontmatterDescriptionDecisions(descriptions=decisions)
