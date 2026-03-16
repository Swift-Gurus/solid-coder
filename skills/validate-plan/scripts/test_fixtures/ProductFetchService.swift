// solid-category: network
// solid-description: Fetches product data from REST API with pagination

import Foundation

protocol ProductReading {
    func fetchAll() async throws -> [Product]
}

final class ProductFetchService: ProductReading {
    func fetchAll() async throws -> [Product] {
        []
    }
}
