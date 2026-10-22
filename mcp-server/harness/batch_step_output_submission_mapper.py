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
    def __init__(self, mappers: BatchOutputSubmissionMappingResolving, flat_mapper: StepOutputSubmissionMapping) -> None:
        self._mappers = mappers
        self._flat_mapper = flat_mapper

    def map(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> StepOutputSubmissionMappingResult:
        if ready and ready[0].submission_id is not None:
            return self._flat_mapper.map(ready, outputs)
        if not ready or ready[0].batch is None:
            return StepOutputSubmissionMappingResult(outputs=outputs)
        return self._mappers.resolve(ready[0].batch.mode).map(ready, outputs)
