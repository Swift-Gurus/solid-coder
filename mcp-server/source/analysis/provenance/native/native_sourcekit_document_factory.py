"""Composes native document sessions using the active LSP compiler context."""

from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys
from typing import Iterator

from harness.pydantic_model_decoder import PydanticModelDecoder
from scoring.yaml_loader import PyYamlLoader
from source.analysis.provenance.bounded_rpc_process_factory import BoundedRpcProcessFactory
from source.analysis.provenance.native.native_sourcekit_cursor_info import NativeSourceKitCursorInfo
from source.analysis.provenance.native.native_sourcekit_document import NativeSourceKitDocument
from source.analysis.provenance.native.sourcekit_compiler_options import SourceKitCompilerOptions
from source.analysis.provenance.stdio_rpc_channel import RpcExchanging
from source.analysis.tree_sitter_syntax_parser import SourceSyntaxParsing
from source.repository_source_snapshot import RepositorySourceSnapshot


"""
solid-name: NativeSourceKitDocumentFactory
solid-category: factory
solid-spec: [SPEC-064]
solid-description: Creates isolated native cursor sessions with the same toolchain, exact source overlay, and compiler settings as the active semantic provider.
"""
class NativeSourceKitDocumentFactory:
    def __init__(
        self,
        command: list[str],
        options: RpcExchanging,
        processes: BoundedRpcProcessFactory,
        artifacts: Path,
    ) -> None:
        self._command = command
        self._options = options
        self._processes = processes
        self._artifacts = artifacts

    @contextmanager
    def open(self, snapshot: RepositorySourceSnapshot, project_root: Path) -> Iterator[SourceSyntaxParsing[int | str, NativeSourceKitCursorInfo]]:
        settings = PydanticModelDecoder(SourceKitCompilerOptions).decode(
            self._options.request("workspace/_sourceKitOptions", {
                "textDocument": {"uri": snapshot.path.as_uri()},
                "prepareTarget": False, "allowFallbackSettings": True,
            }), "semantic compiler settings",
        )
        executable = Path(self._command[0]) if len(self._command) == 1 and self._command[0] != "/usr/bin/sourcekit-lsp" else Path(
            subprocess.run(
                ["xcrun", "--find", "sourcekit-lsp"], check=True,
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        )
        libraries = executable.resolve().parent.parent / "lib"
        candidates = [libraries / "sourcekitd.framework" / "sourcekitd", libraries / "libsourcekitdInProc.so"]
        library = next((path for path in candidates if path.is_file()), None)
        if library is None:
            raise FileNotFoundError("The active Swift toolchain has no native semantic library.")
        with self._processes.open(
            [sys.executable, str(Path(__file__).with_name("server.py")), str(library)],
            settings.working_directory or project_root, self._artifacts / "native-stderr.log",
        ) as rpc:
            rpc.request("native", {"payload": "\n".join([
                "key.request: source.request.editor.open",
                f"key.name: {json.dumps(str(snapshot.path))}",
                f"key.sourcefile: {json.dumps(str(snapshot.path))}",
                f"key.sourcetext: {json.dumps(snapshot.content)}",
                f"key.compilerargs: {json.dumps(settings.compiler_arguments)}",
            ])})
            yield NativeSourceKitDocument(
                path=snapshot.path, compiler_arguments=settings.compiler_arguments,
                rpc=rpc, yaml=PyYamlLoader(), decoder=PydanticModelDecoder(NativeSourceKitCursorInfo),
            )
