from referencing import Registry, Resource, Specification

from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: ReferencingSchemaRegistryFactory
solid-category: factory
solid-spec: [SPEC-057]
solid-description: Prepares operation-schema references for decoding nested output contracts and recursive definitions.
"""
class ReferencingSchemaRegistryFactory(StructuredModelDecoding[Registry]):
    def __init__(self, registry: Registry, specification: Specification) -> None:
        self._registry = registry
        self._specification = specification

    def decode(self, value: object, description: str) -> Registry:
        return self._registry.with_resource(
            "urn:solid-coder:operation-schema",
            Resource.from_contents(value, default_specification=self._specification),
        )
