"""Constructs immutable submission models from validated MCP payloads."""

from typing import cast

from findings.batch_submission import BatchSubmission
from findings.batch_submission_building import BatchSubmissionBuilding
from findings.metric_value import MetricValue
from findings.partial_review_output import PartialReviewOutput
from findings.principle_metrics import PrincipleMetrics
from findings.principle_submission import PrincipleSubmission
from findings.review_unit import ReviewUnit
from findings.review_unit_kind import ReviewUnitKind
from findings.reviewed_file import ReviewedFile
from json_serializer import JsonSerializing


"""
solid-name: McpBatchSubmissionBuilder
solid-category: boundary-adapter
solid-description: Constructs the immutable submission hierarchy from a validated MCP review payload.
"""
class McpBatchSubmissionBuilder(BatchSubmissionBuilding):
    def __init__(self, json_serializer: JsonSerializing) -> None:
        self._json_serializer = json_serializer

    def build(self, validated_payload: object) -> BatchSubmission:
        raw_submissions = cast(dict, validated_payload)
        return BatchSubmission(
            principles=tuple(
                PrincipleSubmission(
                    label=label,
                    output=self._build_output(raw_output),
                )
                for label, raw_output in raw_submissions.items()
            )
        )

    def _build_output(self, raw_output: dict) -> PartialReviewOutput:
        return PartialReviewOutput(
            timestamp=raw_output["timestamp"],
            files=tuple(self._build_file(raw_file) for raw_file in raw_output["files"]),
        )

    def _build_file(self, raw_file: dict) -> ReviewedFile:
        return ReviewedFile(
            file_path=raw_file.get("file_path", ""),
            units=tuple(self._build_unit(raw_unit) for raw_unit in raw_file["units"]),
        )

    def _build_unit(self, raw_unit: dict) -> ReviewUnit:
        return ReviewUnit(
            name=raw_unit["unit_name"],
            kind=ReviewUnitKind(raw_unit["unit_kind"]),
            metrics=tuple(
                self._build_principle_metrics(principle, raw_values)
                for principle, raw_values in raw_unit["metrics"].items()
            ),
            line_start=raw_unit.get("line_start"),
            line_end=raw_unit.get("line_end"),
        )

    def _build_principle_metrics(
        self,
        principle: str,
        raw_values: dict,
    ) -> PrincipleMetrics:
        return PrincipleMetrics(
            principle=principle,
            values=tuple(
                self._build_metric_value(name, raw_measurement)
                for name, raw_measurement in raw_values.items()
            ),
        )

    def _build_metric_value(self, name: str, raw_measurement: dict) -> MetricValue:
        additional_info_json = None
        if "additional-info" in raw_measurement:
            additional_info_json = self._json_serializer.serialize(
                {"value": raw_measurement["additional-info"]}
            )
        return MetricValue(
            name=name,
            value=raw_measurement["value"],
            additional_info_json=additional_info_json,
        )
