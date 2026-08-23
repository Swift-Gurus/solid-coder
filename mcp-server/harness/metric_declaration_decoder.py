"""Decodes workflow metric fields into a typed declaration."""

from harness.metric_declaration import MetricDeclaration
from harness.metric_declaration_decoding import MetricDeclarationDecoding
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: MetricDeclarationDecoder
solid-category: boundary-adapter
solid-spec: [SPEC-039]
solid-description: Maps metric fields from one workflow step into a validated metric declaration.
"""
class MetricDeclarationDecoder(MetricDeclarationDecoding):
    def __init__(
        self,
        decoder: StructuredModelDecoding[MetricDeclaration],
    ) -> None:
        self._decoder = decoder

    def decode(self, raw: dict) -> MetricDeclaration:
        step_id = raw.get("id") or "<unknown>"
        return self._decoder.decode(
            {
                "metric_id": raw.get("metric_id"),
                "observation_id": raw.get("observation_id", "value"),
                "value": raw.get("value"),
                "scoring": raw.get("scoring"),
            },
            f"metric step '{step_id}'",
        )
