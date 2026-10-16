from pydantic import JsonValue
from referencing import Registry

from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: ReferencingJsonSchemaExpander
solid-category: adapter
solid-spec: [SPEC-057]
solid-description: Resolves schema references for addressable nested output fields while preserving recursive definitions and literal annotations.
"""
class ReferencingJsonSchemaExpander(StructuredModelDecoding[JsonValue]):
    def __init__(
        self,
        registries: StructuredModelDecoding[Registry],
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._registries = registries
        self._error_factory = error_factory

    def decode(self, value: object, description: str) -> JsonValue:
        if not isinstance(value, dict):
            raise self._error_factory.create(f"Invalid {description}: expected a schema object")
        registry = self._registries.decode(value, description)
        pending = [registry["urn:solid-coder:operation-schema"]]
        schema_nodes: set[int] = set()
        while pending:
            resource = pending.pop()
            if id(resource.contents) in schema_nodes:
                continue
            schema_nodes.add(id(resource.contents))
            pending.extend(resource.subresources())
        return self._expand(value, registry, frozenset(), schema_nodes)

    def _expand(
        self,
        value: JsonValue,
        registry: Registry,
        active: frozenset[str],
        schema_nodes: set[int],
    ) -> JsonValue:
        if isinstance(value, list):
            return [self._expand(item, registry, active, schema_nodes) for item in value]
        if not isinstance(value, dict):
            return value
        is_schema = id(value) in schema_nodes
        reference = value.get("$ref")
        if is_schema and isinstance(reference, str):
            if reference in active:
                return value
            target = registry.resolver("urn:solid-coder:operation-schema").lookup(reference).contents
            if not isinstance(target, dict):
                raise self._error_factory.create(f"Operation schema reference '{reference}' must resolve to an object")
            value = {**target, **value}
            active = active | {reference}
        return {
            name: item if is_schema and name == "$defs"
            else self._expand(item, registry, active, schema_nodes)
            for name, item in value.items()
        }
