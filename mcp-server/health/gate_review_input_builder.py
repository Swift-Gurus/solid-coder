"""Builds typed review preparation input for prospective writes."""

from __future__ import annotations

from pathlib import Path

from patch_review_context import PatchReviewContext
from review.prepare_review_input import PrepareReviewInput
from source.text_analysis_source import TextAnalysisSource


"""
solid-name: GateReviewInputBuilder
solid-category: service
solid-spec: [SPEC-036, SPEC-041]
solid-description: Prepares typed prospective source input for review.
"""
class GateReviewInputBuilder:
    def build(
        self,
        content: str,
        path: str,
        patch_context: PatchReviewContext | None,
    ) -> PrepareReviewInput:
        target_path = Path(path).resolve()
        context_sources = (
            [
                TextAnalysisSource(
                    text=simulation.content,
                    virtual_path=simulation.file_path,
                )
                for simulation in patch_context.proposed_files
                if Path(simulation.file_path).resolve() != target_path
            ]
            if patch_context is not None
            else []
        )
        return PrepareReviewInput(
            target=TextAnalysisSource(
                text=content,
                virtual_path=path,
            ),
            context_sources=context_sources,
        )
