"""Compiles typed assignments into one model-facing aggregate turn."""

from harness.aggregate_assignment import AggregateAssignment
from harness.aggregate_prompt_rendering import AggregatePromptRendering
from harness.aggregate_response_schema_building import AggregateResponseSchemaBuilding
from harness.compiled_aggregate_turn import CompiledAggregateTurn


"""
solid-name: AggregateTurnCompiler
solid-category: service
solid-spec: [SPEC-045]
solid-description: Coordinates aggregate prompt rendering and exact response-schema generation.
"""
class AggregateTurnCompiler:
    def __init__(
        self,
        prompt_renderer: AggregatePromptRendering,
        schema_builder: AggregateResponseSchemaBuilding,
    ) -> None:
        self._prompt_renderer = prompt_renderer
        self._schema_builder = schema_builder

    def compile(
        self,
        assignments: list[AggregateAssignment],
    ) -> CompiledAggregateTurn:
        return CompiledAggregateTurn(
            prompt=self._prompt_renderer.render(assignments),
            schema=self._schema_builder.build(assignments),
        )
