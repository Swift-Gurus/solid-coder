import Foundation

class ProductCatalog {
    private let storage: UserDefaults
    private let cache: NSCache<NSString, AnyObject>
    private let template: String
    private let formatter: NumberFormatter

    init(storage: UserDefaults, template: String, formatter: NumberFormatter) {
        self.storage = storage
        self.cache = NSCache()
        self.template = template
        self.formatter = formatter
    }

    func save(_ data: Data, key: String) {
        storage.set(data, forKey: key)
        cache.removeObject(forKey: key as NSString)
    }

    func load(key: String) -> Data? {
        if let cached = cache.object(forKey: key as NSString) as? Data { return cached }
        return storage.data(forKey: key)
    }

    func invalidate(key: String) {
        storage.removeObject(forKey: key)
        cache.removeObject(forKey: key as NSString)
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
        items.map { template.replacingOccurrences(of: "{{item}}", with: $0) }
             .joined(separator: "\n")
    }
}
