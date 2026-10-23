"""Counts a complete intermediate workflow collection deterministically."""

from harness.collection_count_input import CollectionCountInput
from harness.collection_count_output import CollectionCountOutput

"""
solid-name: CollectionCountOperation
solid-category: service
solid-spec: [SPEC-057]
solid-description: Derives an intermediate collection size without model arithmetic or rule-specific semantics.
"""


class CollectionCountOperation:
    def execute(self, input_value: CollectionCountInput) -> CollectionCountOutput:
        return CollectionCountOutput(value=len(input_value.values))
