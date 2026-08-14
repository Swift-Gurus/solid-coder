"""Formats typed unit scoring results for compatibility clients."""

from scoring.unit_scoring_result import UnitScoringResult
from scoring.unit_scoring_result_formatting import UnitScoringResultFormatting


"""
solid-name: UnitScoringResultFormatter
solid-category: boundary-adapter
solid-description: Formats typed unit scoring outcomes for compatibility clients.
"""
class UnitScoringResultFormatter(UnitScoringResultFormatting):
    def format(self, result: UnitScoringResult) -> dict:
        response = {
            "metric_id": result.metric_id,
            "final_severity": result.severity.value,
            "band_matched": None,
        }
        if result.error_message is not None:
            response["error"] = result.error_message
        return response
