"""Derives minimal representative values from JSON Schema declarations."""

from rules.schema_minimal_value_resolving import SchemaMinimalValueResolving


"""
solid-name: SchemaMinimalValueResolver
solid-category: service
solid-description: Resolves recursive JSON Schema value declarations into deterministic minimal example values.
"""
class SchemaMinimalValueResolver(SchemaMinimalValueResolving):
    def resolve(self, schema: dict):
        value_type = schema.get("type", "string")
        if value_type == "integer":
            return 0
        if value_type == "string":
            values = schema.get("enum")
            return values[0] if values else "example"
        if value_type == "boolean":
            return False
        if value_type == "array":
            item_properties = schema.get("items", {}).get("properties", {})
            if item_properties:
                return [
                    {
                        name: self.resolve(item_schema)
                        for name, item_schema in item_properties.items()
                    }
                ]
            return []
        if value_type == "object":
            properties = schema.get("properties", {})
            return {
                name: self.resolve(property_schema)
                for name, property_schema in properties.items()
            }
        return "example"
