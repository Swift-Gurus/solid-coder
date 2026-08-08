"""Renders immutable scored review outputs as JSON text."""

from findings.additional_info_decoding import AdditionalInfoDecoding
from findings.metric_value import MetricValue
from findings.partial_review_output import PartialReviewOutput
from findings.partial_review_output_rendering import PartialReviewOutputRendering
from findings.principle_metrics import PrincipleMetrics
from findings.review_unit import ReviewUnit
from findings.reviewed_file import ReviewedFile
from json_serializer import JsonSerializing


"""
solid-name: JsonPartialReviewOutputRenderer
solid-category: boundary-adapter
solid-description: Renders immutable scored review data in the persisted review-output JSON format.
"""
class JsonPartialReviewOutputRenderer(PartialReviewOutputRendering):
    def __init__(
        self,
        serializer: JsonSerializing,
        additional_info_decoder: AdditionalInfoDecoding,
    ) -> None:
        self._serializer = serializer
        self._additional_info_decoder = additional_info_decoder

    def render(self, output: PartialReviewOutput) -> str:
        return self._serializer.serialize(
            {
                "timestamp": output.timestamp,
                "files": [self._file_payload(file) for file in output.files],
            },
            indent=2,
        )

    def _file_payload(self, reviewed_file: ReviewedFile) -> dict:
        return {
            "file_path": reviewed_file.file_path,
            "units": [self._unit_payload(unit) for unit in reviewed_file.units],
        }

    def _unit_payload(self, unit: ReviewUnit) -> dict:
        payload = {
            "unit_name": unit.name,
            "unit_kind": unit.kind.value,
            "metrics": {
                metrics.principle: self._metrics_payload(metrics)
                for metrics in unit.metrics
            },
            "violations": [
                {
                    "rule_id": violation.rule_id,
                    "severity": violation.severity.value,
                }
                for violation in unit.violations
            ],
        }
        if unit.line_start is not None:
            payload["line_start"] = unit.line_start
        if unit.line_end is not None:
            payload["line_end"] = unit.line_end
        return payload

    def _metrics_payload(self, metrics: PrincipleMetrics) -> dict:
        return {
            measurement.name: self._measurement_payload(measurement)
            for measurement in metrics.values
        }

    def _measurement_payload(self, measurement: MetricValue) -> dict:
        payload = {"value": measurement.value}
        if measurement.additional_info_json is None:
            return payload
        additional_info = self._additional_info_decoder.decode(
            measurement.additional_info_json
        )
        if additional_info is not None:
            payload["additional-info"] = additional_info.value
        return payload
