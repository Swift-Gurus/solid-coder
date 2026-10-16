import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, ValidationError
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.schema_references.operation_output_specs_resolver_factory import OperationOutputSpecsResolverFactory
from harness.workflow_data_schema import WorkflowDataSchema
from source.analysis.matching.source_declaration_members import SourceDeclarationMembers


"""
solid-name: RecursiveOutputFixture
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Supplies recursive typed operation output data for schema-reference boundary tests.
"""
class RecursiveOutputFixture(BaseModel):
    name: str
    children: list["RecursiveOutputFixture"] = Field(default_factory=list)


"""
solid-name: SchemaMetadataOutputFixture
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Supplies aliased output fields and literal reference-shaped annotations for schema-boundary tests.
"""
class SchemaMetadataOutputFixture(BaseModel):
    label: str = Field(alias="displayLabel")
    payload: dict[str, str] = Field(
        default={"reference": "default"},
        json_schema_extra={"examples": [{"reference": "example"}]},
    )


"""
solid-name: KeywordNamedOutputFixture
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Supplies a referenced output property whose name is also a JSON-schema annotation keyword.
"""
class KeywordNamedOutputFixture(BaseModel):
    default: RecursiveOutputFixture


"""
solid-name: TestPydanticOperationOutputSpecsResolver
solid-category: unit-test
solid-spec: [SPEC-057]
solid-description: Verifies typed operation schemas expose nested condition fields while retaining valid references and recursive definitions at the serialization boundary.
"""
class TestPydanticOperationOutputSpecsResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = OperationOutputSpecsResolverFactory().make(FlowValidationErrorFactory())

    def test_collection_item_enum_is_visible_to_condition_validation(self) -> None:
        outputs = self.resolver.resolve(SourceDeclarationMembers)
        members = next(output for output in outputs if output.name == "members")

        schema = WorkflowDataSchema.model_validate(members.schema)

        self.assertEqual(schema.type, "array")
        self.assertIsNotNone(schema.items.property("role"))
        self.assertEqual(schema.items.property("role").type, "string")

    def test_nested_member_visibility_is_visible_to_condition_validation(self) -> None:
        outputs = self.resolver.resolve(SourceDeclarationMembers)
        members = next(output for output in outputs if output.name == "members")
        schema = WorkflowDataSchema.model_validate(members.schema)

        reference = schema.items.property("reference")

        self.assertIsNotNone(reference)
        self.assertEqual(reference.property("member").property("visibility").type, "string")

    def test_referenced_members_validate_without_dangling_definition_errors(self) -> None:
        outputs = self.resolver.resolve(SourceDeclarationMembers)
        members = next(output for output in outputs if output.name == "members")

        with self.assertRaises(ValidationError):
            Draft202012Validator(members.schema).validate([{}])

    def test_recursive_output_retains_references_without_infinite_expansion(self) -> None:
        outputs = self.resolver.resolve(RecursiveOutputFixture)
        children = next(output for output in outputs if output.name == "children")

        validator = Draft202012Validator(children.schema)

        validator.validate([{"name": "parent", "children": [{"name": "child"}]}])
        with self.assertRaises(ValidationError):
            validator.validate([{"name": "parent", "children": [{"name": 12}]}])

    def test_resolving_does_not_modify_the_model_schema(self) -> None:
        original = SourceDeclarationMembers.model_json_schema()

        self.resolver.resolve(SourceDeclarationMembers)

        self.assertEqual(SourceDeclarationMembers.model_json_schema(), original)

    def test_alias_does_not_rename_the_serialized_operation_output(self) -> None:
        outputs = self.resolver.resolve(SchemaMetadataOutputFixture)

        self.assertEqual([output.name for output in outputs], ["label", "payload"])
        self.assertEqual(outputs[0].schema["type"], "string")

    def test_default_and_example_values_are_not_treated_as_schema_references(self) -> None:
        schema = SchemaMetadataOutputFixture.model_json_schema(by_alias=False)
        schema["properties"]["payload"]["default"] = {"$ref": "literal-default"}
        schema["properties"]["payload"]["examples"] = [{"$ref": "literal-example"}]
        with patch.object(SchemaMetadataOutputFixture, "model_json_schema", return_value=schema):
            outputs = self.resolver.resolve(SchemaMetadataOutputFixture)
        payload = next(output for output in outputs if output.name == "payload")

        self.assertEqual(payload.schema["default"], {"$ref": "literal-default"})
        self.assertEqual(payload.schema["examples"], [{"$ref": "literal-example"}])

    def test_property_named_like_an_annotation_still_resolves_its_reference(self) -> None:
        outputs = self.resolver.resolve(KeywordNamedOutputFixture)

        schema = WorkflowDataSchema.model_validate(outputs[0].schema)

        self.assertIsNotNone(schema.property("name"))
        self.assertEqual(schema.property("name").type, "string")

    def test_reference_sibling_does_not_weaken_the_referenced_constraint(self) -> None:
        schema = SchemaMetadataOutputFixture.model_json_schema(by_alias=False)
        schema["$defs"] = {"Label": {"type": "string", "minLength": 5}}
        schema["properties"]["label"] = {"$ref": "#/$defs/Label", "minLength": 1}
        with patch.object(SchemaMetadataOutputFixture, "model_json_schema", return_value=schema):
            outputs = self.resolver.resolve(SchemaMetadataOutputFixture)

        validator = Draft202012Validator(outputs[0].schema)

        with self.assertRaises(ValidationError):
            validator.validate("ab")
        validator.validate("valid")
