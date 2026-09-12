"""Composes project review-policy loading."""

from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.project_context import ProjectDirectoryReading
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.review_policy import ReviewPolicy
from harness.review_policy_identity_validator import ReviewPolicyIdentityValidator
from harness.review_policy_loader import ReviewPolicyLoader
from harness.review_policy_parser import ReviewPolicyParser
from harness.sha256_content_hasher import Sha256ContentHasher
from harness.unique_string_validator import UniqueStringValidator
from scoring.yaml_loader import PyYamlLoader


"""
solid-name: ReviewPolicyLoaderFactory
solid-category: service
solid-spec: [SPEC-039]
solid-description: Supplies the configured project review-policy loading capability.
"""
class ReviewPolicyLoaderFactory:

    def __init__(self, project_directory: ProjectDirectoryReading) -> None:
        self._project_directory = project_directory

    def make(self) -> ReviewPolicyLoader:
        error_factory = FlowValidationErrorFactory()
        return ReviewPolicyLoader(
            project_directory=self._project_directory,
            yaml_loader=PyYamlLoader(),
            parser=ReviewPolicyParser(
                decoder=PydanticModelDecoder(model_type=ReviewPolicy),
                validators=[
                    ReviewPolicyIdentityValidator(
                        UniqueStringValidator(error_factory)
                    )
                ],
            ),
            content_hasher=Sha256ContentHasher(),
            error_factory=error_factory,
        )
