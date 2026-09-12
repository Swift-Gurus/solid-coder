"""
solid-name: test_review_policy_loader
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Verifies the singular project review policy is loaded with typed provenance and hashing.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.default_review_policy_resolution import DefaultReviewPolicyResolution
from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.project_context import ProjectDirectory
from harness.project_review_policy_resolution import ProjectReviewPolicyResolution
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.review_policy import ReviewPolicy
from harness.review_policy_identity_validator import ReviewPolicyIdentityValidator
from harness.review_policy_loader import ReviewPolicyLoader
from harness.review_policy_parser import ReviewPolicyParser
from harness.sha256_content_hasher import Sha256ContentHasher
from harness.unique_string_validator import UniqueStringValidator
from scoring.yaml_loader import PyYamlLoader


class TestReviewPolicyLoader(unittest.TestCase):

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project_root = Path(temporary.name)
        error_factory = FlowValidationErrorFactory()
        self.sut = ReviewPolicyLoader(
            project_directory=ProjectDirectory(path=self.project_root),
            yaml_loader=PyYamlLoader(),
            parser=ReviewPolicyParser(
                decoder=PydanticModelDecoder(
                    model_type=ReviewPolicy,
                ),
                validators=[
                    ReviewPolicyIdentityValidator(
                        UniqueStringValidator(error_factory)
                    )
                ],
            ),
            content_hasher=Sha256ContentHasher(),
            error_factory=error_factory,
        )

    def test_absent_project_policy_returns_explicit_default_resolution(self):
        resolution = self.sut.load()

        self.assertIsInstance(resolution, DefaultReviewPolicyResolution)
        self.assertEqual(resolution.policy, ReviewPolicy(version=1))

    def test_loads_only_the_singular_project_policy_path(self):
        policy_path = self.project_root / ".solid-coder" / "policies" / "review.yaml"
        policy_path.parent.mkdir(parents=True)
        authored = "version: 1\nrules:\n  - workflow_id: solid-srp-review\n    enabled: false\n"
        policy_path.write_text(authored)

        resolution = self.sut.load()

        self.assertIsInstance(resolution, ProjectReviewPolicyResolution)
        self.assertEqual(resolution.audit.source_path, policy_path.resolve())
        self.assertEqual(resolution.authored_content, authored)
        self.assertEqual(
            resolution.audit.content_hash,
            hashlib.sha256(authored.encode("utf-8")).hexdigest(),
        )
        self.assertFalse(resolution.policy.rules[0].enabled)

    def test_invalid_project_policy_reports_its_exact_path(self):
        policy_path = self.project_root / ".solid-coder" / "policies" / "review.yaml"
        policy_path.parent.mkdir(parents=True)
        policy_path.write_text("version: 1\nautomatic: true\n")

        with self.assertRaisesRegex(
            FlowValidationError,
            str(policy_path.resolve()),
        ):
            self.sut.load()


if __name__ == "__main__":
    unittest.main()
