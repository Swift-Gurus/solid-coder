"""Prepares model-facing review input from project changes."""

from health.llama.json_deserializer import JsonDeserializing
from pipeline.review_input_preparing import ReviewInputPreparing
from pipeline.skill_runner import SkillRunning


"""
solid-name: ReviewInputPreparer
solid-category: service
solid-description: Prepares structured review input and candidate tags from current project changes.
"""
class ReviewInputPreparer(ReviewInputPreparing):
    def __init__(
        self,
        runner: SkillRunning,
        json_deserializer: JsonDeserializing,
    ) -> None:
        self._runner = runner
        self._json_deserializer = json_deserializer

    def prepare(self, candidate_tags=None) -> dict:
        succeeded, output, error = self._runner.execute(
            "prepare-review-input",
            "prepare-changes.py",
            [],
        )
        if not succeeded:
            return {"error": error}
        prepared = self._json_deserializer.deserialize(output.encode("utf-8"))
        if prepared is None:
            return {"error": f"Could not parse script output: {output}"}
        prepared["candidate_tags"] = candidate_tags or []
        return prepared
