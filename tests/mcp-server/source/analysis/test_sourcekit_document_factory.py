"""Validates exact overlays and cleanup through the production semantic client."""

from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
import subprocess

from source.analysis.provenance.sourcekit_document_factory import SourceKitDocumentFactory
from source.analysis.provenance.native.source_call_reference import SourceCallReference
from source.repository_source_snapshot import RepositorySourceSnapshot


@skipUnless(which("xcrun") or which("sourcekit-lsp"), "Requires installed Swift semantic tooling")
class TestSourceKitDocumentFactory(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="semantic-document-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.path = self.root / "Unwritten.swift"
        self.source = "protocol Service {}\nfunc inspect(_ value: any Service) { _ = value }\n"
        self.snapshot = RepositorySourceSnapshot(
            path=self.path, source_identity=str(self.path), content=self.source,
            content_sha256="fixture",
        )
        self.processes = []
        self.real_popen = subprocess.Popen

    def start_process(self, *args, **kwargs):
        process = self.real_popen(*args, **kwargs)
        self.processes.append(process)
        return process

    def test_one_process_serves_multiple_queries_without_writing_the_document(self):
        with patch("source.analysis.provenance.bounded_rpc_process_factory.subprocess.Popen", side_effect=self.start_process):
            with SourceKitDocumentFactory().open(self.snapshot, self.root) as document:
                contract = document.lookup(self.source.encode().rindex(b"Service"))[0]
                value = document.lookup(self.source.encode().rindex(b"value"))[0]
                self.assertNotEqual(contract.symbol_id, value.symbol_id)
                self.assertEqual(contract.kind, 11)
                self.assertFalse(self.path.exists())
        self.assertEqual(len(self.processes), 1)
        self.assertIsNotNone(self.processes[0].poll())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_timeout_terminates_the_owned_process(self):
        with patch("source.analysis.provenance.bounded_rpc_process_factory.subprocess.Popen", side_effect=self.start_process):
            with self.assertRaisesRegex(TimeoutError, "initialize"):
                with SourceKitDocumentFactory(timeout_seconds=0).open(self.snapshot, self.root):
                    self.fail("An expired session must not yield a document.")
        self.assertEqual(len(self.processes), 1)
        self.assertIsNotNone(self.processes[0].poll())
        self.assertFalse(self.path.exists())

    def test_consumer_failure_still_terminates_the_owned_process(self):
        with patch("source.analysis.provenance.bounded_rpc_process_factory.subprocess.Popen", side_effect=self.start_process):
            with self.assertRaisesRegex(RuntimeError, "consumer"):
                with SourceKitDocumentFactory().open(self.snapshot, self.root):
                    raise RuntimeError("consumer failure")
        self.assertIsNotNone(self.processes[0].poll())

    def test_native_worker_is_lazy_shared_and_closed_after_consumer_failure(self):
        source = """protocol Service {}
struct Provider {
    func first() -> any Service { fatalError() }
    func second() -> any Service { fatalError() }
}
func inspect(_ provider: Provider) {
    _ = provider.first()
    _ = provider.second()
}
"""
        snapshot = RepositorySourceSnapshot(
            path=self.path, source_identity=str(self.path), content=source, content_sha256="fixture",
        )
        with patch("source.analysis.provenance.bounded_rpc_process_factory.subprocess.Popen", side_effect=self.start_process):
            with self.assertRaisesRegex(RuntimeError, "consumer"):
                with SourceKitDocumentFactory().open(snapshot, self.root) as document:
                    self.assertEqual(len(self.processes), 1)
                    for name in [b"first()", b"second()"]:
                        offset = source.encode().rindex(name)
                        symbol = document.lookup(offset)[0]
                        contract = document.return_type(SourceCallReference(offset=offset, symbol_id=symbol.symbol_id))
                        self.assertEqual(contract.kind, "declaration")
                        self.assertIn("Service", contract.symbol_id)
                    raise RuntimeError("consumer failure")
        native_workers = [
            process for process in self.processes
            if any(Path(argument).name == "server.py" for argument in process.args)
        ]
        self.assertEqual(len(native_workers), 1)
        self.assertTrue(all(process.poll() is not None for process in self.processes))
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_tooling_is_explicit_and_does_not_spawn(self):
        with patch("source.analysis.provenance.sourcekit_document_factory.which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "unavailable"):
                with SourceKitDocumentFactory().open(self.snapshot, self.root):
                    self.fail("Missing tooling cannot yield a document.")
