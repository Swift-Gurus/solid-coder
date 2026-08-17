"""Loads the singular project-owned review policy."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Union

from harness.content_hashing import ContentHashing
from harness.default_review_policy_resolution import DefaultReviewPolicyResolution
from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.project_review_policy_resolution import ProjectReviewPolicyResolution
from harness.review_policy_parser import ReviewPolicyParser
from scoring.yaml_loader import YamlLoading

_POLICY_RELATIVE_PATH = Path(".solid-coder") / "policies" / "review.yaml"

ReviewPolicyLoadResult = Union[
    DefaultReviewPolicyResolution,
    ProjectReviewPolicyResolution,
]


"""
solid-name: ReviewPolicyLoader
solid-category: service
solid-spec: [SPEC-039]
solid-description: Loads and validates the project review policy with auditable source content and hashing.
"""
class ReviewPolicyLoader:

    def __init__(
        self,
        project_directory: Callable[[], Path],
        yaml_loader: YamlLoading,
        parser: ReviewPolicyParser,
        content_hasher: ContentHashing,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._project_directory = project_directory
        self._yaml_loader = yaml_loader
        self._parser = parser
        self._content_hasher = content_hasher
        self._error_factory = error_factory

    def load(self) -> ReviewPolicyLoadResult:
        source_path = (self._project_directory() / _POLICY_RELATIVE_PATH).resolve()
        if not source_path.exists():
            return DefaultReviewPolicyResolution()
        try:
            authored_content = source_path.read_text(encoding="utf-8")
            decoded = self._yaml_loader.safe_load(authored_content)
            policy = self._parser.parse(decoded)
        except FlowValidationError as error:
            raise self._error_factory.create(
                f"Invalid review policy '{source_path}': {error}"
            ) from error
        except (OSError, UnicodeError, ValueError) as error:
            raise self._error_factory.create(
                f"Review policy '{source_path}' could not be loaded: {error}"
            ) from error
        return ProjectReviewPolicyResolution(
            policy=policy,
            audit=ProjectReviewPolicyAudit(
                source_path=source_path,
                content_hash=self._content_hasher.hash(
                    authored_content.encode("utf-8")
                ),
            ),
            authored_content=authored_content,
        )
