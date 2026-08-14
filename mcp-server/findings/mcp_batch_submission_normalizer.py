"""Normalizes the compact keyed MCP findings payload."""

from typing import cast

from findings.batch_submission_normalizing import BatchSubmissionNormalizing


"""
solid-name: McpBatchSubmissionNormalizer
solid-category: boundary-adapter
solid-description: Normalizes compact keyed MCP findings into the typed submission hierarchy shape.
"""
class McpBatchSubmissionNormalizer(BatchSubmissionNormalizing):
    def normalize(self, payload: object) -> object:
        submissions = cast(dict, payload)
        return {
            "principles": [
                {
                    "label": label,
                    "output": self._normalize_output(output),
                }
                for label, output in submissions.items()
            ]
        }

    def _normalize_output(self, output: dict) -> dict:
        return {
            "timestamp": output["timestamp"],
            "files": [self._normalize_file(file) for file in output["files"]],
        }

    def _normalize_file(self, file: dict) -> dict:
        return {
            "file_path": file.get("file_path", ""),
            "units": [self._normalize_unit(unit) for unit in file["units"]],
        }

    def _normalize_unit(self, unit: dict) -> dict:
        return {
            "name": unit["unit_name"],
            "kind": unit["unit_kind"],
            "line_start": unit.get("line_start"),
            "line_end": unit.get("line_end"),
            "metrics": [
                {
                    "principle": principle,
                    "values": [
                        {"name": name, **measurement}
                        for name, measurement in measurements.items()
                    ],
                }
                for principle, measurements in unit["metrics"].items()
            ],
        }
