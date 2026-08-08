"""
solid-name: test_active_run_pointer_store
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Validates atomic write, read, and delete operations on active run pointers.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_exists_error import ActiveRunExistsError
from harness.active_run_pointer_store import ActiveRunPointerStore
from harness.session_scoped_active_path_resolver import SessionScopedActivePathResolver


class StubSessionIdReader:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    def read_session_id(self) -> str:
        return self._session_id


class TestActiveRunPointerStore(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.base_dir = Path(self._tmpdir)
        self.store = ActiveRunPointerStore()

    def test_write_creates_active_json_with_run_id(self):
        self.store.write(self.base_dir, "run-abc")

        result = self.store.read(self.base_dir)

        self.assertEqual(result, "run-abc")

    def test_write_raises_active_run_exists_error_when_file_exists(self):
        self.store.write(self.base_dir, "run-first")

        with self.assertRaises(ActiveRunExistsError):
            self.store.write(self.base_dir, "run-second")

    def test_read_returns_run_id_from_existing_file(self):
        self.store.write(self.base_dir, "run-xyz")

        run_id = self.store.read(self.base_dir)

        self.assertEqual(run_id, "run-xyz")

    def test_delete_removes_active_json(self):
        self.store.write(self.base_dir, "run-delete")
        self.store.delete(self.base_dir)

        self.assertFalse((self.base_dir / "active.json").exists())


class TestActiveRunPointerStoreSessionScoping(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.base_dir = Path(self._tmpdir)

    def _store_for(self, session_id: str) -> ActiveRunPointerStore:
        return ActiveRunPointerStore(
            path_resolver=SessionScopedActivePathResolver(session_id_reader=StubSessionIdReader(session_id))
        )

    def test_write_uses_session_scoped_filename_when_session_id_present(self):
        store = self._store_for("session-a")

        store.write(self.base_dir, "run-abc")

        self.assertTrue((self.base_dir / "active-session-a.json").exists())
        self.assertFalse((self.base_dir / "active.json").exists())

    def test_read_returns_run_id_from_session_scoped_file(self):
        store = self._store_for("session-a")
        store.write(self.base_dir, "run-abc")

        self.assertEqual(store.read(self.base_dir), "run-abc")

    def test_two_sessions_do_not_clobber_each_other(self):
        store_a = self._store_for("session-a")
        store_b = self._store_for("session-b")

        store_a.write(self.base_dir, "run-a")
        store_b.write(self.base_dir, "run-b")

        self.assertEqual(store_a.read(self.base_dir), "run-a")
        self.assertEqual(store_b.read(self.base_dir), "run-b")

    def test_delete_only_removes_the_matching_session_file(self):
        store_a = self._store_for("session-a")
        store_b = self._store_for("session-b")
        store_a.write(self.base_dir, "run-a")
        store_b.write(self.base_dir, "run-b")

        store_a.delete(self.base_dir)

        self.assertFalse((self.base_dir / "active-session-a.json").exists())
        self.assertEqual(store_b.read(self.base_dir), "run-b")

    def test_empty_session_id_falls_back_to_plain_active_json(self):
        store = self._store_for("")

        store.write(self.base_dir, "run-abc")

        self.assertTrue((self.base_dir / "active.json").exists())


if __name__ == "__main__":
    unittest.main()
