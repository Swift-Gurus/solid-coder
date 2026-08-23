import Foundation

// solid-name: ExistingCatalogServing
// solid-category: service
// solid-description: Supplies an independent in-memory CatalogServing conformer for previews and tests.
final class ExistingCatalogServing: CatalogServing {
    private var values: [String: Data] = [:]

    func save(_ data: Data, key: String) {
        values[key] = data
    }

    func load(key: String) -> Data? {
        values[key]
    }

    func render(_ value: Double) -> String {
        String(value)
    }

    func format(_ value: Double, precision: Int) -> String {
        String(format: "%.*f", precision, value)
    }

    func present(_ items: [String]) -> String {
        items.joined(separator: ", ")
    }

    func reset() {
        values.removeAll()
    }
}
