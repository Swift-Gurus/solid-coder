"""Owns an isolated semantic process and its exact document overlay."""

from contextlib import contextmanager
from pathlib import Path
from shutil import which
import subprocess
from tempfile import TemporaryDirectory
from typing import ContextManager, Iterator, Protocol, TypeVar

from pydantic import TypeAdapter

from content_length_reader import ContentLengthReader
from content_length_writer import ContentLengthWriter
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.pydantic_type_adapter_decoder import PydanticTypeAdapterDecoder
from harness.thread_pool_executor_factory import ThreadPoolExecutorFactory
from health.llama.timer import MonotonicTimer
from source.analysis.provenance.bounded_rpc_message_reader import BoundedRpcMessageReader
from source.analysis.provenance.rpc_inbound_message import RpcInboundMessage
from source.analysis.provenance.sourcekit_document import SemanticSymbolLookingUp, SourceKitDocument
from source.analysis.provenance.sourcekit_initialization import SourceKitInitialization
from source.analysis.provenance.sourcekit_symbol import SourceKitSymbol
from source.analysis.provenance.stdio_rpc_channel import StdioRpcChannel
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
            with (artifacts / "stderr.log").open("w+b") as stderr:
                process = subprocess.Popen(
                    [*command, "--default-workspace-type", "compilationDatabase",
                     "--scratch-path", str(artifacts / "build"),
                     "--generated-files-path", str(artifacts / "generated")],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                    cwd=project_root,
                )
                with ThreadPoolExecutorFactory().create(max_workers=1) as executor:
                    try:
                        if process.stdin is None or process.stdout is None:
                            raise ConnectionError("Semantic process streams are unavailable.")
                        rpc = StdioRpcChannel(
                            outgoing=process.stdin,
                            reader=BoundedRpcMessageReader(
                                incoming=process.stdout, reader=ContentLengthReader(),
                                decoder=PydanticModelDecoder(RpcInboundMessage),
                                executor=executor,
                            ),
                            writer=ContentLengthWriter(), timer=MonotonicTimer(),
                            timeout_seconds=self._timeout_seconds,
                        )
                        PydanticModelDecoder(SourceKitInitialization).decode(
                            rpc.request("initialize", {
                                "processId": None, "rootUri": project_root.as_uri(),
                                "capabilities": {"general": {"positionEncodings": ["utf-16"]}},
                                "initializationOptions": {"backgroundIndexing": False},
                            }),
                            "semantic initialization",
                        )
                        rpc.notify("initialized", {})
                        rpc.notify("textDocument/didOpen", {"textDocument": {
                            "uri": snapshot.path.as_uri(), "languageId": "swift",
                            "version": 1, "text": snapshot.content,
                        }})
                        yield SourceKitDocument(
                            path=snapshot.path, source=snapshot.content, rpc=rpc,
                            positions=UTF16SourcePositionResolver(),
                            decoder=PydanticTypeAdapterDecoder(TypeAdapter(list[SourceKitSymbol])),
                        )
                    finally:
                        if process.poll() is None:
                            process.terminate()
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait(timeout=5)
                        for stream in (process.stdin, process.stdout):
                            if stream is not None:
                                stream.close()
