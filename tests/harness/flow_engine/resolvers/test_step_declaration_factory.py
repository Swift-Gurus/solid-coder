"""
solid-name: test_step_declaration_factory
solid-category: unit-test
solid-spec: [SPEC-027, SPEC-035]
solid-description: Tests mapping structured workflow input into typed step declarations.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.comparison_condition import ComparisonCondition
from harness.comparison_condition_parser import ComparisonConditionParser
from harness.comparison_operation_parser import ComparisonOperationParser
from harness.composition_condition_parser import CompositionConditionParser
from harness.condition_operator import ConditionOperator
from harness.condition_parser import ConditionParser
from harness.for_each_declaration import ForEachDeclaration
from harness.for_each_declaration_parser import ForEachDeclarationParser
from harness.for_each_mode import ForEachMode
from harness.for_each_reference_parser import ForEachReferenceParser
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.metric_declaration import MetricDeclaration
from harness.metric_declaration_decoder import MetricDeclarationDecoder
from harness.operation_step_contract import OperationStepContract
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.rule_additional_info_output_provider import (
    RuleAdditionalInfoOutputProvider,
)
from harness.rule_step_contract_resolver import RuleStepContractResolver
from harness.step_declaration_factory import StepDeclarationFactory
from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_parser import StepOutputReferenceParser
from harness.workflow_expression_parser import WorkflowExpressionParser
from harness.workflow_expression import WorkflowExpression


class EmptyOperationStepContractResolver:
    def resolve(self, raw: object) -> OperationStepContract:
        return OperationStepContract()


class TestStepDeclarationFactory(unittest.TestCase):
    def setUp(self):
        error_factory = FlowValidationErrorFactory()
        self.sut = StepDeclarationFactory(
            condition_parser=ConditionParser(
                composition_parser=CompositionConditionParser(),
                comparison_parser=ComparisonConditionParser(
                    expression_parser=WorkflowExpressionParser(),
                    operation_parser=ComparisonOperationParser(
                        error_factory
                    ),
                ),
            ),
            for_each_parser=ForEachDeclarationParser(
                reference_parser=ForEachReferenceParser(
                    expression_parser=WorkflowExpressionParser(),
                    reference_parser=StepOutputReferenceParser(),
                ),
                expression_parser=WorkflowExpressionParser(),
            ),
            rule_step_contract_resolver=RuleStepContractResolver(
                metric_decoder=MetricDeclarationDecoder(
                    PydanticModelDecoder(
                        model_type=MetricDeclaration,
                    )
                ),
                additional_info_output=RuleAdditionalInfoOutputProvider(),
                error_factory=error_factory,
            ),
            operation_step_contract_resolver=EmptyOperationStepContractResolver(),
        )

    def test_maps_for_each_expression_to_a_typed_reference(self):
        declaration = self.sut.map(
            {
                "id": "review",
                "prompt": "Review {{item}}",
                "for_each": "{{steps.load.outputs.units}}",
            }
        )

        self.assertEqual(
            declaration.for_each,
            ForEachDeclaration(
                source=StepOutputReference(
                    step_id="load",
                    output_name="units",
                ),
            ),
        )

    def test_maps_batch_for_each_to_a_typed_declaration(self):
        declaration = self.sut.map(
            {
                "id": "review",
                "prompt": "Review every supplied unit",
                "for_each": {
                    "source": "{{steps.load.outputs.units}}",
                    "mode": "batch",
                    "label": "{{item.target.name}}",
                },
            }
        )

        self.assertEqual(declaration.for_each.mode, ForEachMode.BATCH)
        self.assertEqual(
            declaration.for_each.label,
            WorkflowExpression(value="item.target.name"),
        )

    def test_maps_when_to_a_typed_condition_declaration(self):
        declaration = self.sut.map(
            {
                "id": "review",
                "prompt": "Review",
                "when": {
                    "ref": "{{item.language}}",
                    "equals": "swift",
                },
            }
        )

        self.assertEqual(
            declaration.condition,
            ComparisonCondition(
                reference=WorkflowExpression(value="item.language"),
                operator=ConditionOperator.EQUALS,
                expected="swift",
            ),
        )

    def test_maps_process_fields_to_named_attributes(self):
        declaration = self.sut.map(
            {
                "id": "validate",
                "type": "script",
                "script_file": "/package/scripts/validate.py",
                "executor": "python3",
                "args": ["--strict"],
                "timeout_seconds": 30,
                "max_attempts": 2,
            }
        )

        self.assertEqual(declaration.id, "validate")
        self.assertEqual(declaration.type, "script")
        self.assertEqual(declaration.script_file, "/package/scripts/validate.py")
        self.assertEqual(declaration.executor, "python3")
        self.assertEqual(declaration.args, ["--strict"])
        self.assertEqual(declaration.timeout_seconds, 30)
        self.assertEqual(declaration.max_attempts, 2)

    def test_maps_output_mappings_to_output_spec_objects(self):
        declaration = self.sut.map(
            {
                "id": "review",
                "prompt": "Review",
                "outputs": [
                    {
                        "name": "findings",
                        "type": "data",
                        "schema": {"type": "array"},
                    }
                ],
            }
        )

        self.assertEqual(len(declaration.outputs), 1)
        self.assertEqual(declaration.outputs[0].name, "findings")
        self.assertEqual(declaration.outputs[0].schema, {"type": "array"})


if __name__ == "__main__":
    unittest.main()
