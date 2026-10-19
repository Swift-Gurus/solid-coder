"""Keeps a child step's own batch scoped to its materialized workflow instance."""

from pathlib import Path
import sys
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.batch_step_presentation_builder import BatchStepPresentationBuilder
from harness.combined_rule_presentation import CombinedRulePresentation
from harness.expression_evaluating import ExpressionEvaluating
from harness.for_each_declaration import ForEachDeclaration
from harness.for_each_mode import ForEachMode
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.included_workflow_step_identity import IncludedWorkflowStepIdentity
from harness.step_def import StepDef
from harness.step_output_reference import StepOutputReference
from harness.workflow_expression import WorkflowExpression
from harness.workflow_run_context import WorkflowRunContext


class TestNestedBatchScope(TestCase):
    def presentation(self, owner, own_iteration=True, combined=True):
        declaration = ForEachDeclaration(StepOutputReference("prepare", "items"), ForEachMode.BATCH, WorkflowExpression("item.label"))
        instance = IncludedWorkflowInstance(
            alias="reviews.rule", instance_id=owner, source_index=0, source_item=None,
            steps=IncludedWorkflowStepIdentities([IncludedWorkflowStepIdentity("declaration", "classify", "execution")]),
            for_each=declaration,
            combined_presentation=CombinedRulePresentation(group_alias="reviews", rule_alias="rule") if combined else None,
        )
        step = StepDef(id="execution", prompt="Classify this unit's items.", workflow_instance=instance, for_each=declaration if own_iteration else None)
        evaluator = Mock(spec=ExpressionEvaluating)
        evaluator.evaluate.return_value = "item-one"
        return BatchStepPresentationBuilder(evaluator).build(step, declaration, WorkflowRunContext())

    def test_inner_batch_does_not_inherit_outer_combined_rule_group(self):
        first = self.presentation("first")
        second = self.presentation("second")
        self.assertEqual(first.mode.value, "ordinary")
        self.assertNotEqual(first.group, second.group)
        self.assertEqual(first.group, self.presentation("first").group)

    def test_inner_batch_is_instance_scoped_without_combined_presentation_too(self):
        self.assertNotEqual(self.presentation("first", combined=False).group, self.presentation("second", combined=False).group)

    def test_inherited_parent_batch_still_combines_workflow_instances(self):
        first = self.presentation("first", own_iteration=False)
        second = self.presentation("second", own_iteration=False)
        self.assertEqual(first.mode.value, "combined_rules")
        self.assertEqual(first.group, second.group)
