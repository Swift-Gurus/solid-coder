"""Owns an isolated semantic process and its exact document overlay."""

from contextlib import ExitStack, contextmanager
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
from typing import ContextManager, Iterator, Protocol, TypeVar

from pydantic import TypeAdapter

from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.pydantic_type_adapter_decoder import PydanticTypeAdapterDecoder
from source.analysis.provenance.bounded_rpc_process_factory import BoundedRpcProcessFactory
from source.analysis.provenance.file_uri_path_parser import FileUriPathParser
from source.analysis.provenance.native.native_sourcekit_document_factory import NativeSourceKitDocumentFactory
from source.analysis.provenance.native.native_sourcekit_return_type_parser import NativeSourceKitReturnTypeParser
from source.analysis.provenance.native.swift_return_type_reference_parser import SwiftReturnTypeReferenceParser
from source.analysis.provenance.sourcekit_document import SemanticSymbolLookingUp, SourceKitDocument
from source.analysis.provenance.sourcekit_initialization import SourceKitInitialization
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.provenance.sourcekit_symbol_resolution_parser import SourceKitSymbolResolutionParser
from source.analysis.provenance.utf16_source_position_resolver import UTF16SourcePositionResolver
from source.repository_source_snapshot import RepositorySourceSnapshot

SemanticSession = TypeVar("SemanticSession", covariant=True)


"""
solid-name: SemanticDocumentOpening
solid-category: abstraction
solid-spec: [SPEC-064]
solid-description: Contract for opening a bounded semantic session on an exact prospective document.
"""
class SemanticDocumentOpening(Protocol[SemanticSession]):
    def open(self, snapshot: RepositorySourceSnapshot, project_root: Path) -> ContextManager[SemanticSession]: ...


"""
solid-name: SourceKitDocumentFactory
solid-category: factory
solid-spec: [SPEC-064]
solid-description: Creates bounded Swift semantic document sessions.
"""
class SourceKitDocumentFactory(SemanticDocumentOpening[SemanticSymbolLookingUp]):
    def __init__(self, timeout_seconds: float = 30) -> None:
        self._timeout_seconds = timeout_seconds

    @contextmanager
    def open(self, snapshot: RepositorySourceSnapshot, project_root: Path) -> Iterator[SemanticSymbolLookingUp]:
        executable = which("sourcekit-lsp")
        if executable is not None:
            command = [executable]
        elif which("xcrun") is not None:
            command = ["xcrun", "sourcekit-lsp"]
        else:
            raise FileNotFoundError("Swift semantic tooling is unavailable.")
        with TemporaryDirectory(prefix="solid-coder-semantic-") as directory:
            artifacts = Path(directory)
            processes = BoundedRpcProcessFactory(self._timeout_seconds)
            with processes.open(
                [*command, "--default-workspace-type", "compilationDatabase",
                 "--scratch-path", str(artifacts / "build"),
                 "--generated-files-path", str(artifacts / "generated"),
                 "--experimental-feature", "sourcekit-options-request"],
                project_root, artifacts / "stderr.log",
            ) as rpc:
                PydanticModelDecoder(SourceKitInitialization).decode(
                    rpc.request("initialize", {
                        "processId": None, "rootUri": project_root.as_uri(),
                        "capabilities": {"general": {"positionEncodings": ["utf-16"]}},
                        "initializationOptions": {"backgroundIndexing": False},
                    }), "semantic initialization",
                )
                rpc.notify("initialized", {})
                rpc.notify("textDocument/didOpen", {"textDocument": {
                    "uri": snapshot.path.as_uri(), "languageId": "swift",
                    "version": 1, "text": snapshot.content,
                }})
                with ExitStack() as native_scope:
                    yield SourceKitDocument(
                        path=snapshot.path, source=snapshot.content, rpc=rpc,
                        positions=UTF16SourcePositionResolver(),
                        decoder=PydanticTypeAdapterDecoder(TypeAdapter(list[SourceKitSymbol])),
                        return_types=NativeSourceKitReturnTypeParser(
                            session=NativeSourceKitDocumentFactory(command, rpc, processes, artifacts).open(snapshot, project_root),
                            scope=native_scope, references=SwiftReturnTypeReferenceParser(),
                            symbols=SourceKitSymbolResolutionParser(frozenset(), FileUriPathParser()),
                        ),
                    )
