"""Checks that source search rejects ineligible paths before content access."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from harness.sha256_content_hasher import Sha256ContentHasher
from source.repository_source_snapshot import RepositorySourceSnapshot
from source.source_candidate_origin import SourceCandidateOrigin
from source.source_search_context import SourceSearchContext
from source.source_search_input import SourceSearchInput
from source.source_search_operation_factory import SourceSearchOperationFactory
from source.source_search_query import SourceSearchQuery

"""
solid-name: TestSourceSearchFileEligibility
solid-category: unit-test
solid-spec: [SPEC-060]
solid-description: Verifies that source search avoids reading excluded resources and disk files replaced by prospective buffers.
"""


class TestSourceSearchFileEligibility(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        GitWorkingTreeFixture(self.root).initialize()
        self.path = self.root / "Profile.swift"
        self.content = (
            "// solid-name: Profile\n"
            "// solid-description: Loads profile records.\n"
            "struct Profile {}\n"
        )
        self.path.write_text(self.content, encoding="utf-8")
        self.query = SourceSearchQuery(id="profile", terms=["profile"])
        self.operation = SourceSearchOperationFactory().make(
            ProjectDirectory(path=self.root),
        )

    def test_explicit_extensions_exclude_resources_before_reading(self) -> None:
        (self.root / "Profile.json").write_text('{"profile": true}', encoding="utf-8")
        (self.root / "Localizable.strings").write_text(
            '"profile" = "Profile";', encoding="utf-8"
        )

        with patch.object(
            Path, "read_bytes", autospec=True, side_effect=Path.read_bytes
        ) as reads:
            result = self.operation.execute(
                SourceSearchInput(
                    queries=[self.query],
                    included_file_extensions=[".swift"],
                )
            )

        self.assertEqual(reads.call_args_list, [call(self.path)])
        self.assertEqual(
            [candidate.path for candidate in result.candidates], [self.path]
        )

    def test_default_code_search_excludes_localization_and_json_before_reading(
        self,
    ) -> None:
        (self.root / "Profile.json").write_text('{"profile": true}', encoding="utf-8")
        (self.root / "Localizable.xcstrings").write_text(
            '{"profile": {}}', encoding="utf-8"
        )

        with patch.object(
            Path, "read_bytes", autospec=True, side_effect=Path.read_bytes
        ) as reads:
            result = self.operation.execute(SourceSearchInput(queries=[self.query]))

        self.assertEqual(reads.call_args_list, [call(self.path)])
        self.assertEqual(result.files_scanned, 1)

    def test_proposed_source_replaces_disk_without_reading_stale_content(self) -> None:
        prospective = self.content.replace("Loads profile", "Caches profile")
        snapshot = RepositorySourceSnapshot(
            path=self.path,
            source_identity=self.path.name,
            content=prospective,
            content_sha256=Sha256ContentHasher().hash(prospective.encode("utf-8")),
        )

        with patch.object(
            Path, "read_bytes", autospec=True, side_effect=Path.read_bytes
        ) as reads:
            result = self.operation.execute(
                SourceSearchInput(
                    queries=[self.query],
                    context=SourceSearchContext(sources=[snapshot]),
                )
            )

        reads.assert_not_called()
        self.assertEqual(result.candidates[0].origin, SourceCandidateOrigin.PROPOSED)
        self.assertEqual(result.candidates[0].description, "Caches profile records.")

    def test_explicit_extensions_override_the_default_code_policy(self) -> None:
        document = self.root / "Profile.md"
        document.write_text("Profile documentation")

        with patch.object(
            Path, "read_bytes", autospec=True, side_effect=Path.read_bytes
        ) as reads:
            result = self.operation.execute(
                SourceSearchInput(
                    queries=[self.query],
                    included_file_extensions=[".md"],
                )
            )

        self.assertEqual(reads.call_args_list, [call(document)])
        self.assertEqual(
            [candidate.path for candidate in result.candidates], [document]
        )

    def test_explicit_empty_extensions_keep_generic_search_available(self) -> None:
        document = self.root / "Profile.md"
        document.write_text("Profile documentation")

        result = self.operation.execute(
            SourceSearchInput(
                queries=[self.query],
                included_file_extensions=[],
            )
        )

        self.assertEqual(
            {candidate.path for candidate in result.candidates}, {self.path, document}
        )

    def test_eligible_symlink_cannot_bypass_target_extension_filtering(self) -> None:
        resource = self.root / "Profile.json"
        resource.write_text('{"profile": true}')
        (self.root / "Alias.swift").symlink_to(resource)

        with patch.object(
            Path, "read_bytes", autospec=True, side_effect=Path.read_bytes
        ) as reads:
            result = self.operation.execute(SourceSearchInput(queries=[self.query]))

        self.assertEqual(reads.call_args_list, [call(self.path)])
        self.assertEqual(
            [candidate.path for candidate in result.candidates], [self.path]
        )
