"""Validates exact overlays and cleanup through the production semantic client."""

from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
from unittest import TestCase, skipUnless
from unittest.mock import patch
import subprocess

from source.analysis.provenance.sourcekit_document_factory import SourceKitDocumentFactory
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
        with patch("source.analysis.provenance.sourcekit_document_factory.subprocess.Popen", side_effect=self.start_process):
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
        with patch("source.analysis.provenance.sourcekit_document_factory.subprocess.Popen", side_effect=self.start_process):
            with self.assertRaisesRegex(TimeoutError, "initialize"):
                with SourceKitDocumentFactory(timeout_seconds=0).open(self.snapshot, self.root):
                    self.fail("An expired session must not yield a document.")
        self.assertEqual(len(self.processes), 1)
        self.assertIsNotNone(self.processes[0].poll())
        self.assertFalse(self.path.exists())

    def test_consumer_failure_still_terminates_the_owned_process(self):
        with patch("source.analysis.provenance.sourcekit_document_factory.subprocess.Popen", side_effect=self.start_process):
            with self.assertRaisesRegex(RuntimeError, "consumer"):
                with SourceKitDocumentFactory().open(self.snapshot, self.root):
                    raise RuntimeError("consumer failure")
        self.assertIsNotNone(self.processes[0].poll())

    def test_missing_tooling_is_explicit_and_does_not_spawn(self):
        with patch("source.analysis.provenance.sourcekit_document_factory.which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "unavailable"):
                with SourceKitDocumentFactory().open(self.snapshot, self.root):
                    self.fail("Missing tooling cannot yield a document.")
