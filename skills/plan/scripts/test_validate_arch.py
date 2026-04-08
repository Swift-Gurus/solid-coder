#!/usr/bin/env python3
"""Tests for validate-arch.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), 'validate-arch.py')
SCHEMA = os.path.join(os.path.dirname(__file__), '..', 'arch.schema.json')


def run(data, extra_args=None):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        path = f.name
    try:
        cmd = [sys.executable, SCRIPT, path] + (extra_args or [])
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(path)


def valid_arch():
    """Minimal valid arch.json."""
    return {
        "spec_summary": "Open a project folder in a new window",
        "mode": "default",
        "components": [
            {
                "name": "WindowOpening",
                "category": "abstraction",
                "stack": [],
                "responsibility": "Contract for opening a project in a new window.",
                "interfaces": ["WindowOpening"],
                "dependencies": [],
                "produces": [],
                "fields": []
            },
            {
                "name": "WindowManager",
                "category": "service",
                "stack": ["swiftui"],
                "responsibility": "Manages open windows and deduplicates by project path.",
                "interfaces": [],
                "dependencies": ["WindowOpening"],
                "produces": [],
                "fields": []
            },
            {
                "name": "ProjectState",
                "category": "model",
                "stack": [],
                "responsibility": "Represents the state of an open project.",
                "interfaces": [],
                "dependencies": [],
                "produces": [],
                "fields": ["id: String", "path: URL", "name: String"]
            }
        ],
        "wiring": [
            {"from": "WindowManager", "to": "WindowOpening", "via": "init"}
        ],
        "composition_root": "AppFactory"
    }


class TestValidArch(unittest.TestCase):

    def test_valid_passes(self):
        code, out, _ = run(valid_arch())
        self.assertEqual(code, 0)
        self.assertIn("All validations passed", out)

    def test_valid_with_schema(self):
        code, out, _ = run(valid_arch(), ['--schema', SCHEMA])
        self.assertEqual(code, 0)
        self.assertIn("All validations passed", out)


class TestDependencyResolution(unittest.TestCase):

    def test_unresolved_dependency(self):
        data = valid_arch()
        data['components'][1]['dependencies'] = ['NonExistentProtocol']
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("NonExistentProtocol", out)
        self.assertIn("no component exposes it", out)

    def test_dependency_resolved_by_another_component(self):
        """Dependency resolved by a different component's interfaces — should pass."""
        code, out, _ = run(valid_arch())
        self.assertEqual(code, 0)


class TestWiringValidation(unittest.TestCase):

    def test_wiring_to_unknown_interface(self):
        data = valid_arch()
        data['wiring'] = [{"from": "WindowManager", "to": "GhostProtocol", "via": "init"}]
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("GhostProtocol", out)
        self.assertIn("not exposed by any component", out)

    def test_wiring_from_unknown_component(self):
        data = valid_arch()
        data['wiring'] = [{"from": "PhantomService", "to": "WindowOpening", "via": "init"}]
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("PhantomService", out)
        self.assertIn("no component with that name", out)

    def test_empty_wiring_passes(self):
        data = valid_arch()
        data['wiring'] = []
        data['components'][1]['dependencies'] = []
        code, out, _ = run(data)
        self.assertEqual(code, 0)


class TestDataModelConstraints(unittest.TestCase):

    def test_model_empty_fields(self):
        data = valid_arch()
        data['components'][2]['fields'] = []
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("ProjectState", out)
        self.assertIn("empty fields[]", out)

    def test_model_non_empty_interfaces(self):
        data = valid_arch()
        data['components'][2]['interfaces'] = ["SomeProtocol"]
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("non-empty interfaces[]", out)

    def test_model_non_empty_dependencies(self):
        data = valid_arch()
        data['components'][2]['dependencies'] = ["SomeDep"]
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("non-empty dependencies[]", out)

    def test_model_non_empty_produces(self):
        data = valid_arch()
        data['components'][2]['produces'] = ["Something"]
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("non-empty produces[]", out)


class TestStackVocabulary(unittest.TestCase):

    def test_unknown_stack_is_warning_not_error(self):
        data = valid_arch()
        data['components'][1]['stack'] = ['unknown-framework']
        code, out, _ = run(data)
        self.assertEqual(code, 0)  # warning, not error
        self.assertIn("WARNING", out)
        self.assertIn("unknown-framework", out)

    def test_valid_stacks_no_warning(self):
        data = valid_arch()
        data['components'][1]['stack'] = ['swiftui', 'combine']
        code, out, _ = run(data)
        self.assertEqual(code, 0)
        self.assertNotIn("WARNING", out)


class TestMultipleErrors(unittest.TestCase):

    def test_multiple_errors_all_reported(self):
        data = valid_arch()
        # Two unresolved dependencies
        data['components'][1]['dependencies'] = ['MissingA', 'MissingB']
        data['wiring'] = [{"from": "WindowManager", "to": "MissingA", "via": "init"}]
        code, out, _ = run(data)
        self.assertEqual(code, 1)
        self.assertIn("MissingA", out)
        self.assertIn("MissingB", out)


class TestSchemaValidation(unittest.TestCase):

    def test_missing_required_field(self):
        data = valid_arch()
        del data['spec_summary']
        code, out, _ = run(data, ['--schema', SCHEMA])
        self.assertEqual(code, 1)
        self.assertIn("Schema", out)

    def test_invalid_wiring_via(self):
        data = valid_arch()
        data['wiring'][0]['via'] = 'injection'  # not in enum
        code, out, _ = run(data, ['--schema', SCHEMA])
        self.assertEqual(code, 1)
        self.assertIn("Schema", out)


if __name__ == '__main__':
    unittest.main(verbosity=2)
