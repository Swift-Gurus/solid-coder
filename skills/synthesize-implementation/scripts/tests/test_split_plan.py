"""Tests for skills/synthesize-implementation/scripts/split-plan.py.

Contract:
  - Without --arch: all items treated as implementations, split by dependency level,
    chunk files named xx-implementations.json
  - With --arch: items classified by component category (model/enum/typealias →
    foundation) and test_cases type (unit/integration → test, ui → ui_test)
  - foundation items: aggregated into a single chunk
  - implementation items: split by dependency level
  - test / ui_test items: each in a single chunk, after implementations
  - Unknown component (not in arch) defaults to implementation
  - Category matching is case-insensitive
  - Shared fields (spec_summary, matched_tags, acceptance_criteria) in every chunk
  - Empty plan exits 0 cleanly
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "split-plan.py"


def run_script(plan_data, arch_data=None):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        plan_path = tmp / "implementation-plan.json"
        plan_path.write_text(json.dumps(plan_data), encoding="utf-8")
        out_dir = tmp / "chunks"

        cmd = [sys.executable, str(SCRIPT), str(plan_path), "--output-dir", str(out_dir)]
        if arch_data is not None:
            arch_path = tmp / "arch.json"
            arch_path.write_text(json.dumps(arch_data), encoding="utf-8")
            cmd += ["--arch", str(arch_path)]

        result = subprocess.run(cmd, capture_output=True, text=True)

        chunks = {}
        if out_dir.exists():
            for f in sorted(out_dir.glob("*.json")):
                chunks[f.name] = json.loads(f.read_text(encoding="utf-8"))

        return result.returncode, chunks, result.stderr


def make_plan(items, spec_summary="test spec", matched_tags=None, acceptance_criteria=None):
    return {
        "spec_summary": spec_summary,
        "matched_tags": matched_tags or ["srp"],
        "acceptance_criteria": acceptance_criteria or ["global criterion"],
        "plan_items": items,
        "reconciliation_decisions": [],
        "summary": {"create": len(items), "modify": 0, "reuse": 0},
    }


def make_item(id_, component="SomeService", depends_on=None, test_cases=None):
    item = {
        "id": id_,
        "action": "create",
        "component": component,
        "directive": f"implement {id_}",
        "depends_on": depends_on or [],
        "notes": "",
        "acceptance_criteria": [],
    }
    if test_cases is not None:
        item["test_cases"] = test_cases
    return item


def make_arch(*components):
    """components: (name, category) pairs."""
    return {
        "spec_summary": "test",
        "components": [
            {
                "name": name, "category": cat, "stack": [],
                "responsibility": "", "interfaces": [],
                "dependencies": [], "produces": [], "fields": [],
            }
            for name, cat in components
        ],
        "wiring": [],
        "composition_root": "",
    }


def unit_tc():
    return {"type": "unit", "description": "t", "given": "g", "when": "w", "expect": "e"}


def ui_tc():
    return {"type": "ui", "description": "t", "given": "g", "when": "w", "expect": "e"}


class TestNoArch(unittest.TestCase):
    """Without arch.json all items are implementations, split by dependency level."""

    def test_single_item_in_one_implementations_chunk(self):
        rc, chunks, _ = run_script(make_plan([make_item("plan-001")]))
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-implementations.json"])

    def test_two_independent_items_stay_in_one_chunk(self):
        rc, chunks, _ = run_script(make_plan([make_item("plan-001"), make_item("plan-002")]))
        self.assertEqual(rc, 0)
        self.assertEqual(len(chunks["01-implementations.json"]["plan_items"]), 2)

    def test_dependent_items_split_by_level(self):
        items = [
            make_item("plan-001"),
            make_item("plan-002", depends_on=["plan-001"]),
            make_item("plan-003", depends_on=["plan-002"]),
        ]
        rc, chunks, _ = run_script(make_plan(items))
        self.assertEqual(rc, 0)
        self.assertEqual(
            list(chunks),
            ["01-implementations.json", "02-implementations.json", "03-implementations.json"],
        )

    def test_shared_fields_copied_into_every_chunk(self):
        items = [make_item("plan-001"), make_item("plan-002", depends_on=["plan-001"])]
        rc, chunks, _ = run_script(
            make_plan(items, spec_summary="My spec", matched_tags=["swiftui"],
                      acceptance_criteria=["criterion A"])
        )
        self.assertEqual(rc, 0)
        for chunk in chunks.values():
            self.assertEqual(chunk["spec_summary"], "My spec")
            self.assertIn("swiftui", chunk["matched_tags"])
            self.assertIn("criterion A", chunk["acceptance_criteria"])


class TestWithArch(unittest.TestCase):
    def test_model_goes_to_foundations(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="ProductModel")]),
            make_arch(("ProductModel", "model")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-foundations.json"])

    def test_enum_goes_to_foundations(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="Status")]),
            make_arch(("Status", "enum")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-foundations.json"])

    def test_typealias_goes_to_foundations(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="UserID")]),
            make_arch(("UserID", "typealias")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-foundations.json"])

    def test_service_goes_to_implementations(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="ProductService")]),
            make_arch(("ProductService", "service")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-implementations.json"])

    def test_unit_test_item_goes_to_tests(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="Tests", test_cases=[unit_tc()])]),
            make_arch(("Tests", "test")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-tests.json"])

    def test_ui_test_item_goes_to_ui_tests(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="UITests", test_cases=[ui_tc()])]),
            make_arch(("UITests", "test")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-ui-tests.json"])

    def test_mixed_test_cases_ui_wins(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="Mixed", test_cases=[unit_tc(), ui_tc()])]),
            make_arch(("Mixed", "test")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-ui-tests.json"])

    def test_multiple_foundations_aggregated_into_one_chunk(self):
        items = [
            make_item("plan-001", component="ModelA"),
            make_item("plan-002", component="ModelB"),
            make_item("plan-003", component="EnumC"),
        ]
        rc, chunks, _ = run_script(
            make_plan(items),
            make_arch(("ModelA", "model"), ("ModelB", "model"), ("EnumC", "enum")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-foundations.json"])
        self.assertEqual(len(chunks["01-foundations.json"]["plan_items"]), 3)

    def test_full_mixed_group_order(self):
        arch = make_arch(
            ("ProductModel", "model"),
            ("ProductService", "service"),
            ("ProductViewModel", "viewmodel"),
            ("ProductTests", "test"),
            ("ProductUITests", "test"),
        )
        items = [
            make_item("plan-001", component="ProductModel"),
            make_item("plan-002", component="ProductService", depends_on=["plan-001"]),
            make_item("plan-003", component="ProductViewModel", depends_on=["plan-002"]),
            make_item("plan-004", component="ProductTests", test_cases=[unit_tc()]),
            make_item("plan-005", component="ProductUITests", test_cases=[ui_tc()]),
        ]
        rc, chunks, _ = run_script(make_plan(items), arch)
        self.assertEqual(rc, 0)
        names = list(chunks)
        self.assertEqual(names[0], "01-foundations.json")
        self.assertTrue(all("implementations" in n for n in names[1:-2]))
        self.assertIn("tests.json", names[-2])
        self.assertIn("ui-tests.json", names[-1])

    def test_impl_levels_are_relative_to_implementations_only(self):
        """An impl item that depends only on a foundation should be level 0,
        not level 1 — foundation deps don't inflate implementation chunk count."""
        arch = make_arch(
            ("ModelA", "model"),          # foundation
            ("ServiceA", "service"),       # impl, depends on ModelA
            ("ServiceB", "service"),       # impl, depends on ServiceA
        )
        items = [
            make_item("plan-001", component="ModelA"),
            make_item("plan-002", component="ServiceA", depends_on=["plan-001"]),
            make_item("plan-003", component="ServiceB", depends_on=["plan-002"]),
        ]
        rc, chunks, _ = run_script(make_plan(items), arch)
        self.assertEqual(rc, 0)
        # ServiceA depends only on a foundation → impl level 0
        # ServiceB depends on ServiceA (impl level 0) → impl level 1
        # So: 01-foundations, 02-implementations (ServiceA), 03-implementations (ServiceB)
        self.assertEqual(list(chunks), [
            "01-foundations.json",
            "02-implementations.json",
            "03-implementations.json",
        ])
        impl0 = chunks["02-implementations.json"]["plan_items"]
        impl1 = chunks["03-implementations.json"]["plan_items"]
        self.assertEqual([i["component"] for i in impl0], ["ServiceA"])
        self.assertEqual([i["component"] for i in impl1], ["ServiceB"])

    def test_unknown_component_defaults_to_implementation(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="UnknownType")]),
            make_arch(("OtherComponent", "service")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-implementations.json"])

    def test_category_matching_is_case_insensitive(self):
        rc, chunks, _ = run_script(
            make_plan([make_item("plan-001", component="Data")]),
            make_arch(("Data", "Model")),
        )
        self.assertEqual(rc, 0)
        self.assertEqual(list(chunks), ["01-foundations.json"])


class TestEdgeCases(unittest.TestCase):
    def test_empty_plan_exits_cleanly(self):
        rc, chunks, _ = run_script(make_plan([]))
        self.assertEqual(rc, 0)
        self.assertEqual(chunks, {})

    def test_missing_arch_file_falls_back_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            plan_path = tmp / "implementation-plan.json"
            plan_path.write_text(json.dumps(make_plan([make_item("plan-001")])))
            out_dir = tmp / "chunks"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(plan_path),
                 "--output-dir", str(out_dir), "--arch", str(tmp / "nonexistent.json")],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue((out_dir / "01-implementations.json").exists())


if __name__ == "__main__":
    unittest.main()
