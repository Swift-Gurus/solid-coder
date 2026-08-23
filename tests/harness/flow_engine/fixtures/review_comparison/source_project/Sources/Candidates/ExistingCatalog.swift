import Foundation

// solid-name: ExistingCatalog
// solid-category: service
// solid-description: Persists cached catalog data and provides the complete catalog formatting and presentation behavior.
final class ExistingCatalog {
    private let storage: UserDefaults
    private let cache: NSCache<NSString, AnyObject>
    private let template: String
    private let formatter: NumberFormatter

    init(
        storage: UserDefaults,
        cache: NSCache<NSString, AnyObject>,
        template: String,
        formatter: NumberFormatter
    ) {
        self.storage = storage
        self.cache = cache
        self.template = template
        self.formatter = formatter
    }

    func save(_ data: Data, key: String) {
        storage.set(data, forKey: key)
        cache.removeObject(forKey: key as NSString)
    }

    func load(key: String) -> Data? {
        if let cached = cache.object(forKey: key as NSString) as? Data {
            return cached
        }
        return storage.data(forKey: key)
    }

    func render(_ value: Double) -> String {
        template.replacingOccurrences(
            of: "{{value}}",
            with: formatter.string(from: NSNumber(value: value)) ?? ""
        )
    }

    func format(_ value: Double, precision: Int) -> String {
        formatter.minimumFractionDigits = precision
        return formatter.string(from: NSNumber(value: value)) ?? String(value)
    }

    func present(_ items: [String]) -> String {
        items.map {
            template.replacingOccurrences(of: "{{item}}", with: $0)
        }.joined(separator: "\n")
    }

    func reset() {
        fatalError("Reset is unsupported")
    }
}
