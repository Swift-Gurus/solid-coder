from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict


Result = TypeVar("Result", bound=BaseModel)


"""
solid-name: OperationResult
solid-category: model
solid-spec: [SPEC-040, SPEC-057]
solid-description: Carries a complete typed operation result as one named workflow output for binding and ordered fan-in.
"""
class OperationResult(BaseModel, Generic[Result]):
    model_config = ConfigDict(extra="forbid", frozen=True)

    result: Result
