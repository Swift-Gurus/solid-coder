"""Checks real repository boundaries before review and search content access."""

from pathlib import Path
from unittest.mock import patch

import pytest
from git_working_tree_fixture import GitWorkingTreeFixture
from harness.project_context import ProjectDirectory
from health.config.hc_config_core import find_repository_root
from search.codebase_searcher_factory import CodebaseSearcherFactory
from source.analyze_source_input import AnalyzeSourceInput
from source.file_analysis_source import FileAnalysisSource
from source.repository_target_resolver import RepositoryTargetResolver
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from utils.prompt_builder import PlainTextFileReader


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    GitWorkingTreeFixture(root).initialize()
    (root / "Sources").mkdir()
    return root


@pytest.mark.parametrize("target", ["Sources/New.swift", "Sources/../New.swift"])
def test_relative_targets_use_repository_root_from_nested_directory(repository, target):
    resolved = RepositoryTargetResolver(find_repository_root).resolve(
        repository / "Sources", Path(target)
    )

    assert resolved == (repository / target).resolve()


@pytest.mark.parametrize(
    "target", ["../Outside.swift", "../project-sibling/Outside.swift"]
)
def test_parent_and_similarly_prefixed_sibling_targets_are_rejected(repository, target):
    with pytest.raises(ValueError, match="outside repository"):
        RepositoryTargetResolver(find_repository_root).resolve(repository, Path(target))


def test_no_git_root_is_rejected_before_source_reader_is_called(tmp_path):
    operation = SourceAnalysisOperationFactory().make(ProjectDirectory(path=tmp_path))

    with (
        patch.object(PlainTextFileReader, "read") as reader,
        pytest.raises(ValueError, match="No Git repository"),
    ):
        operation.execute(
            AnalyzeSourceInput(source=FileAnalysisSource(path="File.swift"))
        )

    reader.assert_not_called()


@pytest.mark.parametrize("link", [False, True])
def test_file_analysis_rejects_absolute_and_symlink_escapes_before_reading(
    repository, link
):
    outside = repository.parent / "Outside.swift"
    outside.write_text("struct Outside {}", encoding="utf-8")
    target = outside
    if link:
        target = repository / "Link.swift"
        target.symlink_to(outside)
    operation = SourceAnalysisOperationFactory().make(ProjectDirectory(path=repository))

    with (
        patch.object(PlainTextFileReader, "read") as reader,
        pytest.raises(ValueError, match="outside repository"),
    ):
        operation.execute(AnalyzeSourceInput(source=FileAnalysisSource(path=target)))

    reader.assert_not_called()


def test_nested_git_root_is_used_instead_of_outer_repository(repository):
    nested = repository / "nested"
    nested.mkdir()
    GitWorkingTreeFixture(nested).initialize()

    with pytest.raises(ValueError, match="outside repository"):
        RepositoryTargetResolver(find_repository_root).resolve(
            nested, repository / "Outer.swift"
        )


def test_real_worktree_marker_is_supported(repository):
    git = GitWorkingTreeFixture(repository)
    git.run("commit", "--allow-empty", "-m", "initial")
    worktree = repository.parent / "worktree"
    git.run("worktree", "add", "--detach", str(worktree))

    resolved = RepositoryTargetResolver(find_repository_root).resolve(
        worktree, Path("New.swift")
    )

    assert (worktree / ".git").is_file()
    assert resolved == (worktree / "New.swift").resolve()


@pytest.mark.parametrize("operation", ["glob", "definition"])
def test_production_file_search_rejects_an_outside_directory_before_reading(
    repository, operation
):
    search = CodebaseSearcherFactory().make_file_search(
        ProjectDirectory(path=repository)
    )
    outside = repository.parent / "project-sibling"
    outside.mkdir()
    (outside / "Outside.swift").write_text("struct Outside {}", encoding="utf-8")

    with (
        patch.object(Path, "read_text") as reader,
        pytest.raises(ValueError, match="outside repository"),
    ):
        if operation == "glob":
            search.glob_by_name("*.swift", str(outside))
        else:
            search.grep_by_name("Outside", str(outside))

    reader.assert_not_called()


def test_glob_parent_escape_is_rejected_before_enumeration(repository):
    search = CodebaseSearcherFactory().make_file_search(
        ProjectDirectory(path=repository)
    )

    with (
        patch.object(Path, "read_text") as reader,
        pytest.raises(ValueError, match="outside repository"),
    ):
        search.glob_by_name("../*.swift")

    reader.assert_not_called()
