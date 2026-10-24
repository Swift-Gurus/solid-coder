import tempfile
import unittest
from pathlib import Path

from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from source.analysis.operations.discover_source_declaration_input import (
    DiscoverSourceDeclarationInput,
)
from source.analysis.operations.source_declaration_discovery_operation_factory import (
    SourceDeclarationDiscoveryOperationFactory,
)
from source.file_analysis_source import FileAnalysisSource
from source.prepare_search_targets_input import PrepareSearchTargetsInput
from source.prepare_search_targets_operation_factory import (
    PrepareSearchTargetsOperationFactory,
)
from source.search_target_granularity import SearchTargetGranularity
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)
from source.source_search_context import SourceSearchContext

"""
solid-name: TestSourceDeclarationContextOperation
solid-category: integration-test
solid-spec: [SPEC-057]
solid-description: Verifies bounded definition and extension context uses authoritative source, excludes private members and conformers, and preserves unresolved ownership.
"""


class TestSourceDeclarationContextOperation(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        GitWorkingTreeFixture(self.root).initialize()
        self.interface = self.root / "Reading.swift"
        self.extension = self.root / "Reading+Helpers.swift"
        self.interface.write_text("protocol Reading { func read() }\n")
        self.extension.write_text(
            "extension Reading { var extra: Int { 1 }; private var hidden: Int { 2 } }\n"
        )
        (self.root / "Store.swift").write_text(
            "struct Store: Reading { func conformerOnly() {} }\n"
        )
        project = ProjectDirectory(path=self.root)
        self.discover = SourceDeclarationDiscoveryOperationFactory(project).make()
        self.registration = next(
            entry
            for entry in SourceOperationRegistrationsFactory(project).make()
            if entry.name == "source.declaration_context"
        )

    def prepare(self, path: Path, replace_disk: bool = False, exclusions=None):
        prepared = (
            PrepareSearchTargetsOperationFactory()
            .make(ProjectDirectory(path=self.root))
            .execute(
                PrepareSearchTargetsInput(
                    source=FileAnalysisSource(path=path),
                    granularity=SearchTargetGranularity.UNIT,
                )
            )
        )
        if replace_disk:
            path.write_text("struct StaleDisk {}\n")
        discovery = self.discover.execute(
            DiscoverSourceDeclarationInput(
                target=prepared.targets[0],
                context=SourceSearchContext(sources=[prepared.snapshot]),
                follow_related_declarations=False,
            )
        )
        values = {"discovery": discovery}
        if exclusions is not None:
            values["excluded_visibilities"] = exclusions
        return self.registration.handler.execute(
            self.registration.input_model.model_validate(values)
        )

    def test_interface_context_excludes_private_same_line_helpers_and_conformers(
        self,
    ) -> None:
        result = self.prepare(self.interface, exclusions=["private", "fileprivate"])

        self.assertEqual(
            [item.reference.member.name for item in result.members], ["read", "extra"]
        )
        self.assertIn("var extra: Int { 1 }", result.context)
        self.assertNotRegex(result.context, "hidden|conformerOnly|Store")
        self.assertEqual(result.limitations, [])

    def test_extension_target_resolves_to_definition_and_combines_members(self) -> None:
        result = self.prepare(self.extension, exclusions=["private", "fileprivate"])

        self.assertEqual(result.kind.value, "protocol")
        self.assertEqual(result.declaration.source_identity, str(self.interface))
        self.assertIn("func read()", result.context)
        self.assertEqual(
            {item.reference.member.name for item in result.members}, {"read", "extra"}
        )

    def test_prospective_extension_content_wins_over_disk(self) -> None:
        result = self.prepare(self.extension, replace_disk=True)

        self.assertIn("var extra: Int { 1 }", result.context)
        self.assertNotIn("StaleDisk", result.context)

    def test_ambiguous_extension_target_is_unavailable_without_guessing(self) -> None:
        (self.root / "Other.swift").write_text("protocol Reading { func other() }\n")

        result = self.prepare(self.extension)

        self.assertIsNone(result.declaration)
        self.assertEqual(result.members, [])
        self.assertTrue(result.limitations)

    def test_missing_extension_definition_is_unavailable(self) -> None:
        self.interface.unlink()

        result = self.prepare(self.extension)

        self.assertIsNone(result.declaration)
        self.assertTrue(result.limitations)

    def test_concrete_extension_preserves_kind_for_workflow_applicability(self) -> None:
        self.interface.write_text("struct Reading {}\n")

        result = self.prepare(self.extension)

        self.assertEqual(result.kind.value, "struct")

    def test_empty_interface_preserves_definition_without_invented_members(
        self,
    ) -> None:
        self.interface.write_text("protocol Reading {}\n")
        self.extension.unlink()

        result = self.prepare(self.interface)

        self.assertEqual(result.kind.value, "protocol")
        self.assertEqual(result.members, [])
        self.assertEqual(result.limitations, [])

    def test_visibility_filter_is_opt_in_and_applies_to_members_and_rendered_source(
        self,
    ) -> None:
        unfiltered = self.prepare(self.interface)
        filtered = self.prepare(self.interface, exclusions=["private"])

        self.assertIn(
            "hidden", [item.reference.member.name for item in unfiltered.members]
        )
        self.assertIn("hidden", unfiltered.context)
        self.assertNotIn(
            "hidden", [item.reference.member.name for item in filtered.members]
        )
        self.assertNotIn("hidden", filtered.context)

    def test_batch_labels_distinguish_matching_local_member_identities_across_files(
        self,
    ) -> None:
        (self.root / "Reading+More.swift").write_text(
            "extension Reading { var other: Int { 2 } }\n"
        )

        result = self.prepare(self.interface, exclusions=["private", "fileprivate"])

        members = [
            item
            for item in result.members
            if item.reference.member.name in {"extra", "other"}
        ]
        self.assertEqual(len(members), 2)
        self.assertEqual(
            members[0].reference.member.identity, members[1].reference.member.identity
        )
        self.assertNotEqual(members[0].label, members[1].label)
        self.assertEqual(
            len({item.label for item in result.members}), len(result.members)
        )
        self.assertTrue(
            all("label" in item for item in result.model_dump(mode="json")["members"])
        )
