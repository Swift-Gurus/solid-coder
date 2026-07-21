"""
solid-name: test_active_run_pointer_store
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Validates atomic write, read, and delete operations on active run pointers.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_exists_error import ActiveRunExistsError
from harness.active_run_pointer_store import ActiveRunPointerStore


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


if __name__ == "__main__":
    unittest.main()
