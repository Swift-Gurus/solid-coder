"""Defines the sealed source-reference alternatives for collection metrics."""

from harness.step_output_reference import StepOutputReference
from harness.workflow_output_reference import WorkflowOutputReference

CollectionSourceReference = StepOutputReference | WorkflowOutputReference
