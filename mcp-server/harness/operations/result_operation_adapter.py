from typing import Generic, TypeVar

from harness.operation_handling import OperationHandling
from harness.operations.operation_result import OperationResult
from pydantic import BaseModel

Input = TypeVar("Input", bound=BaseModel)
Result = TypeVar("Result", bound=BaseModel)


"""
solid-name: ResultOperationAdapter
solid-category: service
solid-spec: [SPEC-040, SPEC-057]
solid-description: Exposes an existing typed operation result as a single bindable workflow output without changing the underlying service.
"""


class ResultOperationAdapter(
    OperationHandling[Input, OperationResult[Result]],
    Generic[Input, Result],
):
    def __init__(
        self,
        operation: OperationHandling[Input, Result],
        result_type: type[OperationResult[Result]],
    ) -> None:
        self._operation = operation
        self._result_type = result_type

    def execute(self, operation_input: Input) -> OperationResult[Result]:
        return self._result_type(result=self._operation.execute(operation_input))
