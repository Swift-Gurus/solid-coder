"""Validates typed review-rule match declarations."""

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_selection import RuleSelection


"""
solid-name: RuleMatchValidator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Rejects ambiguous or non-normalized review-rule match declarations before execution.
"""
class RuleMatchValidator:

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def validate(self, declaration: RuleMatchDeclaration) -> None:
        self._validate_selection(
            "file_extensions",
            declaration.file_extensions,
        )
        self._validate_selection("unit_kinds", declaration.unit_kinds)
        self._validate_selection("tags", declaration.tags)
        self._validate_extensions(declaration.file_extensions)
        self._validate_tags(declaration.tags)

    def _validate_selection(
        self,
        dimension: str,
        selection: RuleSelection,
    ) -> None:
        authored = [*selection.included, *selection.excluded]
        if len(authored) != len(set(authored)):
            overlap = set(selection.included).intersection(selection.excluded)
            if overlap:
                raise self._error_factory.create(
                    f"Rule match '{dimension}' contains values that are both included and excluded"
                )
            raise self._error_factory.create(
                f"Rule match '{dimension}' contains a duplicate value"
            )

    def _validate_extensions(self, selection: RuleSelection[str]) -> None:
        for extension in [*selection.included, *selection.excluded]:
            if (
                len(extension) < 2
                or not extension.startswith(".")
                or extension != extension.lower()
                or extension != extension.strip()
                or any(character.isspace() for character in extension)
            ):
                raise self._error_factory.create(
                    f"Rule match file extension '{extension}' must be a normalized lowercase suffix beginning with '.'"
                )

    def _validate_tags(self, selection: RuleSelection[str]) -> None:
        for tag in [*selection.included, *selection.excluded]:
            if (
                not tag
                or tag != tag.lower()
                or tag != tag.strip()
                or any(character.isspace() for character in tag)
            ):
                raise self._error_factory.create(
                    f"Rule match tag '{tag}' must be one normalized lowercase word"
                )
