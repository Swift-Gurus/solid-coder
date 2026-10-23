"""Defines the flat flow-next output envelope."""

from harness.submissions.flat_submission_record import FlatSubmissionRecord
from pydantic import BaseModel, ConfigDict

"""
solid-name: FlatSubmissionEnvelope
solid-category: model
solid-spec: [SPEC-068]
solid-description: Represents the ordered addressed results supplied in a flat workflow submission.
"""


class FlatSubmissionEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    submissions: list[FlatSubmissionRecord]
