"""Locks the bundled LSP boundary between model judgment and MCP arithmetic."""

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[3]


"""
solid-name: TestLSPClassificationContract
solid-category: integration-test
solid-spec: [SPEC-064]
solid-description: Verifies the real LSP workflow classifies evidence without model arithmetic, duplicated relationship normalization, or empty counting markers.
"""
class TestLSPClassificationContract(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = yaml.safe_load(
            (ROOT / "workflows/review/rules/lsp/workflow.yaml").read_text()
        )

    def test_model_instructions_classify_without_arithmetic(self) -> None:
        prompts = "\n".join(step.get("prompt", "") for step in self.workflow["steps"])
        self.assertNotIn("**Count", prompts)
        self.assertNotIn("**Calculate percentage", prompts)
        self.assertIn("NEW_GUARD", prompts)
        self.assertIn("WEAKENED_POSTCONDITION", prompts)
        self.assertIn("INVARIANT_VIOLATION", prompts)

    def test_relationship_evidence_is_classified_once_without_result_copying(self) -> None:
        child = yaml.safe_load(
            (ROOT / "workflows/review/rules/lsp/relationship-review/workflow.yaml").read_text()
        )
        self.assertEqual([step["id"] for step in child["steps"]], ["inspect_candidate"])
        prompt = next(step["prompt"] for step in self.workflow["steps"]
                      if step.get("id") == "classify_relationship_violations")
        self.assertNotIn("Normalize", prompt)
        self.assertNotIn("already submitted by the child reviews", prompt)
        self.assertIn("completed repository inspections", prompt)

    def test_intermediate_counts_consume_real_observations_once(self) -> None:
        counts = [step for step in self.workflow["steps"]
                  if step.get("operation") == "collection.count"]
        for step in counts:
            with self.subTest(step=step["id"]):
                self.assertNotEqual(step["with"]["values"], [])
                self.assertNotIn("for_each", step)
