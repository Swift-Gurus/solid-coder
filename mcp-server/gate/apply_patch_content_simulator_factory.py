"""Constructs apply-patch content simulators."""

from add_content_extractor import AddContentExtractor
from apply_patch_content_simulator import ApplyPatchContentSimulator
from apply_patch_parser import ApplyPatchParser
from hunk_applicator import HunkApplicator
from patch_entry_selector import PatchEntrySelector
from patch_entry_simulator import PatchEntrySimulator
from patch_files_simulating import PatchFilesSimulating
from patch_format_parser import PatchFormatParser
from path_file_system_reader import PathFileSystemReader


"""
solid-name: ApplyPatchContentSimulatorFactory
solid-category: factory
solid-description: Creates simulators for apply-patch file content.
solid-tags: [hook]
"""
class ApplyPatchContentSimulatorFactory:
    def create(self) -> PatchFilesSimulating:
        parser = ApplyPatchParser(
            format_parser=PatchFormatParser(),
            content_extractor=AddContentExtractor(),
            hunk_applicator=HunkApplicator(),
        )
        return ApplyPatchContentSimulator(
            entry_selector=PatchEntrySelector(parser=parser),
            entry_simulator=PatchEntrySimulator(
                parser=parser,
                file_reader=PathFileSystemReader(),
            ),
        )
