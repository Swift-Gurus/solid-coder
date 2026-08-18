"""Creates workflow-step declarations from structured input."""

from __future__ import annotations

from harness.condition_parsing import ConditionParsing
from harness.for_each_reference_parsing import ForEachReferenceParsing
from harness.rule_step_contract_resolving import RuleStepContractResolving
from harness.step_declaration import StepDeclaration
from harness.step_declaration_mapping import StepDeclarationMapping


"""
solid-name: StepDeclarationFactory
solid-category: factory
solid-spec: [SPEC-027, SPEC-030, SPEC-035, SPEC-039]
solid-description: Creates unvalidated workflow-step declarations from structured input.
"""
class StepDeclarationFactory(StepDeclarationMapping):
    def __init__(
        self,
        condition_parser: ConditionParsing,
        for_each_parser: ForEachReferenceParsing,
        rule_step_contract_resolver: RuleStepContractResolving,
    ) -> None:
        self._condition_parser = condition_parser
        self._for_each_parser = for_each_parser
        self._rule_step_contract_resolver = rule_step_contract_resolver

    def map(self, raw: dict) -> StepDeclaration:
        rule_contract = self._rule_step_contract_resolver.resolve(raw)
        return StepDeclaration(
            id=raw.get("id"),
            type=raw.get("type", "agent"),
            prompt=raw.get("prompt"),
            depends_on=raw.get("depends_on"),
            outputs=rule_contract.outputs,
            for_each=(
                self._for_each_parser.parse(
                    raw.get("id") or "<unknown>",
                    raw["for_each"],
                )
                if raw.get("for_each") is not None
                else None
            ),
            condition=(
                self._condition_parser.parse(raw["when"])
                if raw.get("when") is not None
                else None
            ),
            mode=raw.get("mode"),
            prompt_file=raw.get("prompt_file"),
            command=raw.get("command"),
            script_file_reference=raw.get("file"),
            script_file=raw.get("script_file"),
            executor=raw.get("executor"),
            args=raw.get("args"),
            timeout_seconds=raw.get("timeout_seconds"),
            max_attempts=raw.get("max_attempts", 3),
            source_file=raw.get("__source_file"),
            metric=rule_contract.metric,
        )
