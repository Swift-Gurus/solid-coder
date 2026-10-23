"""Defines invocation of a dynamically registered typed operation."""

from typing import Protocol

from harness.operation_registration import OperationRegistration
from harness.workflow_context_values import WorkflowContextValues
from pydantic import BaseModel

"""
solid-name: OperationInvoking
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for invoking a registered operation from typed workflow input values.
"""


class OperationInvoking(Protocol):
    def invoke(
        self,
        registration: OperationRegistration,
        inputs: WorkflowContextValues[object],
    ) -> BaseModel: ...
