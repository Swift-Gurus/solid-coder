"""Defines the simulated result of one file operation in an apply_patch command."""

from dataclasses import dataclass


"""
solid-name: PatchFileSimulation
solid-category: value-object
solid-description: Carries one affected file's post-patch content and original content into independent gate review.
solid-tags: [hook]
"""
@dataclass(frozen=True)
class PatchFileSimulation:
    file_path: str
    content: str
    existing_content: str
    low_risk: bool
