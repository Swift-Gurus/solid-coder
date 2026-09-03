"""Maps batch outputs through their presentation-mode capability."""

from harness.batch_output_submission_mapping_resolving import (
    BatchOutputSubmissionMappingResolving,
)
from harness.models import StepInstance
from harness.step_output_submission_mapping import StepOutputSubmissionMapping
from harness.step_output_submission_mapping_result import (
    StepOutputSubmissionMappingResult,
)


"""
solid-name: BatchStepOutputSubmissionMapper
solid-category: service
solid-spec: [SPEC-042]
solid-description: Translates model-facing batch outputs according to their typed presentation mode.
"""
class BatchStepOutputSubmissionMapper(StepOutputSubmissionMapping):
    def __init__(self, mappers: BatchOutputSubmissionMappingResolving) -> None:
        self._mappers = mappers

    def map(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> StepOutputSubmissionMappingResult:
        if not ready or ready[0].batch is None:
            return StepOutputSubmissionMappingResult(outputs=outputs)
        return self._mappers.resolve(ready[0].batch.mode).map(ready, outputs)
