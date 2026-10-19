"""Checks installed Swift semantic evidence without writing the reviewed source."""

import json
from pathlib import Path
from queue import Empty, Queue
from shutil import which
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
from time import monotonic
from types import SimpleNamespace
import unittest

from content_length_reader import ContentLengthReader
from content_length_writer import ContentLengthWriter


"""
solid-name: TestSourceKitSymbolContract
solid-category: integration-test
solid-spec: [SPEC-064]
solid-description: Probes the installed Swift semantic service for declaration and type provenance on an unwritten source document.
"""
@unittest.skipUnless(which("xcrun"), "Swift semantic contract requires the Xcode toolchain")
class TestSourceKitSymbolContract(unittest.TestCase):
    def setUp(self) -> None:
        temporary = TemporaryDirectory(prefix="sourcekit-contract-")
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.stderr = (self.workspace / "sourcekit-stderr.log").open("wb")
        self.addCleanup(self.stderr.close)
        self.process = subprocess.Popen(
            [
                "xcrun", "sourcekit-lsp",
                "--scratch-path", str(self.workspace / "build"),
                "--generated-files-path", str(self.workspace / "generated"),
            ],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
            cwd=self.workspace,
        )
        self.addCleanup(self._close)
        self.responses = Queue()
        self.reader = Thread(target=self._read, daemon=True)
        self.reader.start()
        self.request_id = 0
        initialized = self._request("initialize", {
            "processId": None,
            "rootUri": self.workspace.as_uri(),
            "capabilities": {"general": {"positionEncodings": ["utf-16"]}},
        })
        self.assertIsNone(getattr(initialized, "error", None), initialized)
        self._notify("initialized", {})
        self.path = self.workspace / "Unwritten.swift"
        self.source = (
            "import Foundation\n"
            "protocol Service {}\n"
            "func inspect(_ service: any Service, response: URLResponse) {\n"
            " _ = service\n"
            " _ = response as? HTTPURLResponse\n"
            "}\n"
        )
        self._notify("textDocument/didOpen", {"textDocument": {
            "uri": self.path.as_uri(), "languageId": "swift",
            "version": 1, "text": self.source,
        }})

    def _read(self) -> None:
        try:
            while self.process.stdout is not None:
                raw = ContentLengthReader().read(self.process.stdout, b"")
                if raw is None:
                    return
                # Wire-boundary decoding; test assertions use attributes.
                response = json.loads(
                    json.dumps(raw), object_hook=lambda fields: SimpleNamespace(**fields),
                )
                self.responses.put(response)
        except Exception as error:
            self.responses.put(error)

    def _notify(self, method: str, params: dict) -> None:
        ContentLengthWriter().write(self.process.stdin, {
            "jsonrpc": "2.0", "method": method, "params": params,
        })

    def _request(self, method: str, params: dict) -> SimpleNamespace:
        self.request_id += 1
        ContentLengthWriter().write(self.process.stdin, {
            "jsonrpc": "2.0", "id": self.request_id,
            "method": method, "params": params,
        })
        deadline = monotonic() + 30
        while True:
            try:
                response = self.responses.get(timeout=max(0, deadline - monotonic()))
            except Empty:
                self.fail(
                    f"SourceKit timed out on {method}: "
                    + (self.workspace / "sourcekit-stderr.log").read_text()
                )
            if isinstance(response, Exception):
                raise response
            if getattr(response, "method", None) is not None:
                if getattr(response, "id", None) is not None:
                    ContentLengthWriter().write(self.process.stdin, {
                        "jsonrpc": "2.0", "id": response.id,
                        "error": {"code": -32601, "message": "Unsupported test-client request"},
                    })
                continue
            if getattr(response, "id", None) == self.request_id:
                return response

    def _at(self, method: str, line: int, token: str) -> SimpleNamespace:
        text = self.source.splitlines()[line]
        character = len(text[:text.index(token)].encode("utf-16-le")) // 2
        return self._request(method, {
            "textDocument": {"uri": self.path.as_uri()},
            "position": {"line": line, "character": character},
        })

    def _close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout):
            if stream is not None:
                stream.close()
        if hasattr(self, "reader"):
            self.reader.join(timeout=2)

    def test_unwritten_document_exposes_symbol_provenance(self) -> None:
        local = self._at("textDocument/symbolInfo", 2, "Service")
        sdk = self._at("textDocument/symbolInfo", 2, "URLResponse")
        destination = self._at("textDocument/symbolInfo", 4, "HTTPURLResponse")
        value = self._at("textDocument/symbolInfo", 3, "service")

        self.assertFalse(self.path.exists())
        self.assertIsNone(getattr(local, "error", None), local)
        self.assertEqual(local.result[0].name, "Service")
        self.assertEqual(local.result[0].bestLocalDeclaration.uri, self.path.as_uri())
        self.assertEqual(value.result[0].name, "service")
        self.assertNotEqual(value.result[0].usr, local.result[0].usr)
        self.assertEqual(sdk.result[0].name, "URLResponse")
        self.assertEqual(destination.result[0].name, "HTTPURLResponse")
        self.assertIs(sdk.result[0].isSystem, True)
        self.assertIs(destination.result[0].isSystem, True)
        self.assertIs(local.result[0].isSystem, False)
        self._request("shutdown", {})
        self._notify("exit", {})

    def test_type_lookup_never_substitutes_the_variable_declaration(self) -> None:
        value_type = self._at("textDocument/typeDefinition", 3, "service")

        self.assertIsNone(getattr(value_type, "error", None), value_type)
        # This toolchain returns null for the existential. A future toolchain
        # may resolve it, but a variable location is not a type declaration.
        if value_type.result is not None:
            self.assertEqual(len(value_type.result), 1)
            self.assertEqual(value_type.result[0].uri, self.path.as_uri())
            self.assertEqual(value_type.result[0].range.start.line, 1)
            self.assertEqual(value_type.result[0].range.start.character, 9)
        self.assertFalse(self.path.exists())
        self._request("shutdown", {})
        self._notify("exit", {})
