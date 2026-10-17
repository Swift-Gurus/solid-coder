"""Verifies new-interface evidence using the production source parser."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "mcp-server"))

from source.analysis.operations.verify_introduced_interfaces_operation import VerifyIntroducedInterfacesOperation
from source.path_source_bytes_reader import PathSourceBytesReader
from source.source_analysis_operation_factory import SourceAnalysisOperationFactory
from source.text_analysis_source import TextAnalysisSource
from harness.path_builder import PathBuilder
from harness.sha256_content_hasher import Sha256ContentHasher


@pytest.fixture
def reader():
    return Mock(wraps=PathSourceBytesReader())


@pytest.fixture
def operation(reader):
    return VerifyIntroducedInterfacesOperation(
        reader=reader,
        analyzer=SourceAnalysisOperationFactory().make(),
        paths=PathBuilder(),
        hasher=Sha256ContentHasher(),
    )


@pytest.mark.parametrize("original", [None, "", "struct Existing {}\n"])
def test_identifies_only_new_interfaces_in_the_proposed_source(tmp_path, original, operation):
    path = tmp_path / "Feature.swift"
    if original is not None:
        path.write_text(original, encoding="utf-8")

    result = operation.execute(TextAnalysisSource(
        text=(original or "") + "protocol Reading { func read() }\nstruct NewValue {}\n",
        virtual_path=str(path),
    ))

    assert len(result.verified_interfaces) == 1
    assert result.verified_interfaces[0].source_identity == str(path)
    assert result.reasoning
    assert result.evidence
    assert "sha256" in result.evidence


def test_existing_and_new_interfaces_in_one_file_are_distinguished(tmp_path, operation):
    path = tmp_path / "Feature.swift"
    path.write_text("protocol Existing { func read() }\n", encoding="utf-8")

    result = operation.execute(TextAnalysisSource(
        text=path.read_text() + "protocol Added { func save() }\n",
        virtual_path=str(path),
    ))

    assert len(result.verified_interfaces) == 1
    assert "Added" in result.verified_interfaces[0].unit_identity


@pytest.mark.parametrize("original,proposed", [
    ("protocol Reading {}", "protocol Reading { func read() }"),
    ("protocol Reading {", "protocol Added {}"),
    ("", "protocol Added {"),
])
def test_existing_or_incompletely_parsed_interfaces_are_not_verified_new(tmp_path, original, proposed, operation):
    path = tmp_path / "Feature.swift"
    path.write_text(original, encoding="utf-8")

    result = operation.execute(TextAnalysisSource(text=proposed, virtual_path=str(path)))

    assert result.verified_interfaces == []
    assert result.reasoning


def test_unreadable_original_is_not_treated_as_a_missing_file(tmp_path, reader, operation):
    reader.read.side_effect = PermissionError("Access denied")

    result = operation.execute(TextAnalysisSource(text="protocol Added {}", virtual_path=str(tmp_path / "Feature.swift")))

    assert result.verified_interfaces == []
    assert "Access denied" in result.evidence
