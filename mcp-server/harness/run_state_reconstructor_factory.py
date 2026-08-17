"""Assembles the production run-state reconstruction pipeline."""

from harness.attempt_failed_transition import AttemptFailedTransition
from harness.comparison_condition_parser import ComparisonConditionParser
from harness.comparison_operation_parser import ComparisonOperationParser
from harness.composition_condition_parser import CompositionConditionParser
from harness.condition_parser import ConditionParser
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.run_state_builder import RunStateBuilder
from harness.run_state_event_router import RunStateEventRouter
from harness.run_state_reconstructor import RunStateReconstructor
from harness.run_status_transition import RunStatusTransition
from harness.step_completed_transition import StepCompletedTransition
from harness.step_instance_output_aggregator import StepInstanceOutputAggregator
from harness.step_outputs_builder import StepOutputsBuilder
from harness.step_rejected_transition import StepRejectedTransition
from harness.step_skipped_transition import StepSkippedTransition
from harness.step_started_transition import StepStartedTransition
from harness.turn_counted_transition import TurnCountedTransition
from harness.workflow_condition_evaluated_transition import (
    WorkflowConditionEvaluatedTransition,
)
from harness.workflow_expression_parser import WorkflowExpressionParser


def make_run_state_reconstructor() -> RunStateReconstructor:
    attempt_failed = AttemptFailedTransition()
    error_factory = FlowValidationErrorFactory()
    condition_parser = ConditionParser(
        composition_parser=CompositionConditionParser(),
        comparison_parser=ComparisonConditionParser(
            expression_parser=WorkflowExpressionParser(),
            operation_parser=ComparisonOperationParser(error_factory),
        ),
    )
    return RunStateReconstructor(
        state_builder=RunStateBuilder(),
        event_router=RunStateEventRouter(
            transitions={
                "step_started": StepStartedTransition(),
                "step_completed": StepCompletedTransition(
                    step_outputs_builder=StepOutputsBuilder(),
                    output_aggregator=StepInstanceOutputAggregator(),
                ),
                "step_skipped": StepSkippedTransition(
                    condition_parser=condition_parser,
                ),
                "workflow_condition_evaluated": WorkflowConditionEvaluatedTransition(
                    condition_parser=condition_parser,
                ),
                "turn_counted": TurnCountedTransition(),
                "run_completed": RunStatusTransition(status="done"),
                "run_timed_out": RunStatusTransition(status="timed_out"),
                "step_attempt_failed": attempt_failed,
                "step_rejected": StepRejectedTransition(attempt_transition=attempt_failed),
                "run_failed": RunStatusTransition(status="failed"),
            }
        ),
    )
