"""Exercises semantic binding on exact prospective buffers, without writing them."""

from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory
import unittest

from harness.project_context import ProjectDirectory
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory
from source.analysis.provenance.resolve_type_inspections_input import ResolveTypeInspectionsInput
from source.analysis.provenance.source_type_inspection_operation_factory import SourceTypeInspectionOperationFactory
from source.text_analysis_source import TextAnalysisSource


@unittest.skipUnless(which("xcrun"), "Requires the installed Swift semantic service")
class TestTypeInspectionProvenance(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory(prefix="inspection-provenance-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".git").mkdir()
        self.path = self.root / "Unwritten.swift"
        self.operation = SourceTypeInspectionOperationFactory(ProjectDirectory(path=self.root)).make()

    def resolve(self, source):
        prepared = PrepareReviewOperationFactory().make().execute(PrepareReviewInput(
            target=TextAnalysisSource(text=source, virtual_path=str(self.path)),
        ))
        unit = next(unit for unit in prepared.units if unit.target.name == "Consumer")
        result = self.operation.execute(ResolveTypeInspectionsInput(
            target=unit.target, context=prepared.source_context,
            file_extension=unit.applicability.file_extension,
        ))
        self.assertFalse(self.path.exists())
        return result

    def test_owned_value_contract_is_distinct_from_destination_and_parameter(self):
        result = self.resolve("""protocol Service {}
struct Concrete: Service {}
struct Consumer {
    func inspect(_ service: any Service) {
        _ = service as? Concrete
    }
}
""")
        self.assertEqual(len(result.inspections), 1)
        inspection = result.inspections[0]
        self.assertEqual(inspection.contract.ownership, "developer")
        self.assertEqual(inspection.destination.ownership, "developer")
        self.assertNotEqual(inspection.contract.resolution.symbol_id, inspection.value.resolution.symbol_id)
        self.assertNotEqual(inspection.contract.resolution.symbol_id, inspection.destination.resolution.symbol_id)
        self.assertTrue(inspection.verified)
        self.assertEqual(inspection.contract.declaration_path, self.path)

    def test_sdk_contract_does_not_reclassify_project_parameter_as_external(self):
        result = self.resolve("""import Foundation
struct Consumer {
    func inspect(_ response: URLResponse) {
        _ = response as? HTTPURLResponse
    }
}
""")
        inspection = result.inspections[0]
        self.assertEqual(inspection.contract.ownership, "external")
        self.assertEqual(inspection.destination.ownership, "external")
        self.assertEqual(inspection.value.ownership, "developer")
        self.assertEqual(inspection.contract.resolution.kind, "sdk")

    def test_unresolved_inferred_contract_is_not_a_compliant_empty_inventory(self):
        result = self.resolve("""struct Consumer {
    func inspect() {
        let value = missingProvider()
        _ = value as? String
    }
}
""")
        self.assertEqual(len(result.inspections), 1)
        self.assertFalse(result.inspections[0].verified)
        self.assertEqual(result.inspections[0].contract.ownership, "unknown")
        self.assertTrue(result.inspections[0].limitations)

    def test_sdk_method_result_preserves_call_and_return_contract_provenance(self):
        result = self.resolve("""import Foundation
struct Consumer {
    func inspect(_ cache: NSCache<NSString, AnyObject>, key: String) {
        _ = cache.object(forKey: key as NSString) as? Data
    }
}
""")
        inspection = next(
            item for item in result.inspections
            if item.inspection.operand == "cache.object(forKey: key as NSString)"
        )
        self.assertTrue(inspection.verified, inspection.limitations)
        self.assertEqual(inspection.value.ownership, "external")
        self.assertEqual(inspection.contract.ownership, "external")
        self.assertEqual(inspection.destination.ownership, "external")
        self.assertNotEqual(
            inspection.value.resolution.symbol_id,
            inspection.contract.resolution.symbol_id,
        )
        self.assertEqual(result.limitations, [])

    def test_owned_method_result_resolves_its_return_contract_not_the_receiver(self):
        result = self.resolve("""protocol Service {}
struct Concrete: Service {}
struct Provider {
    func make() -> any Service { Concrete() }
}
struct Consumer {
    func inspect(_ provider: Provider) {
        _ = provider.make() as? Concrete
    }
}
""")
        inspection = result.inspections[0]
        self.assertTrue(inspection.verified, inspection.limitations)
        self.assertEqual(inspection.value.ownership, "developer")
        self.assertEqual(inspection.contract.ownership, "developer")
        self.assertEqual(inspection.destination.ownership, "developer")
        self.assertIn("Service", inspection.contract.resolution.symbol_id)
        self.assertNotEqual(
            inspection.value.resolution.symbol_id,
            inspection.contract.resolution.symbol_id,
        )

    def test_sdk_generic_method_can_return_a_project_owned_contract(self):
        result = self.resolve("""import Foundation
class Service {}
class Concrete: Service {}
struct Consumer {
    func inspect(_ cache: NSCache<NSString, Service>, key: String) {
        _ = cache.object(forKey: key as NSString) as? Concrete
    }
}
""")
        inspection = next(
            item for item in result.inspections
            if item.inspection.operand == "cache.object(forKey: key as NSString)"
        )
        self.assertTrue(inspection.verified, inspection.limitations)
        self.assertEqual(inspection.value.ownership, "external")
        self.assertEqual(inspection.contract.ownership, "developer")
        self.assertEqual(inspection.destination.ownership, "developer")
        self.assertIn("Service", inspection.contract.resolution.symbol_id)
        self.assertEqual(inspection.contract.declaration_path, self.path)

    def test_overloaded_call_uses_the_selected_return_contract(self):
        result = self.resolve("""protocol Service {}
struct Concrete: Service {}
struct Provider {
    func make(_ value: Int) -> any Service { Concrete() }
    func make(_ value: String) -> String { value }
}
struct Consumer {
    func inspect(_ provider: Provider) {
        _ = provider.make(1) as? Concrete
    }
}
""")
        inspection = result.inspections[0]
        self.assertTrue(inspection.verified, inspection.limitations)
        self.assertEqual(inspection.contract.ownership, "developer")
        self.assertIn("Service", inspection.contract.resolution.symbol_id)

    def test_unicode_offsets_preserve_the_inspected_binding(self):
        result = self.resolve("""protocol Service {}
struct Concrete: Service {}
struct Consumer {
    func inspect(_ service: any Service) {
        let emoji = "🧪"; _ = service as? Concrete
    }
}
""")
        self.assertTrue(result.inspections[0].verified)
        self.assertEqual(result.inspections[0].contract.ownership, "developer")
        self.assertEqual(result.inspections[0].inspection.operand, "service")

    def test_empty_complete_inventory_needs_no_semantic_process(self):
        result = self.resolve("struct Consumer { func run() {} }")
        self.assertEqual(result.inspections, [])
        self.assertEqual(result.limitations, [])
