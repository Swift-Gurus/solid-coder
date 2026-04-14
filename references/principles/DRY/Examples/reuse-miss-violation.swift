// DRY-1 Violation: Reuse Miss
// A new type was created when an existing type already covers the responsibility.

// --- Existing in codebase (Shared/Services/DataFetchService.swift) ---

protocol DataFetching {
    func fetch<T: Decodable>(from endpoint: String) async throws -> T
}

final class DataFetchService: DataFetching {
    private let session: URLSessionProtocol

    init(session: URLSessionProtocol) {
        self.session = session
    }

    func fetch<T: Decodable>(from endpoint: String) async throws -> T {
        guard let url = URL(string: endpoint) else { throw FetchError.invalidURL }
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode(T.self, from: data)
    }
}

// --- New code (Features/Products/ProductLoader.swift) ---
// 🔥 DRY-1 Violation: ProductLoader duplicates DataFetchService's responsibility

final class ProductLoader {
    private let session: URLSessionProtocol

    init(session: URLSessionProtocol) {
        self.session = session
    }

    func loadProducts(from endpoint: String) async throws -> [Product] {
        guard let url = URL(string: endpoint) else { throw FetchError.invalidURL }
        let (data, _) = try await session.data(from: url)
        return try JSONDecoder().decode([Product].self, from: data)
    }
}

// Analysis:
// - ProductLoader responsibility: fetch and decode data from network
// - DataFetchService responsibility: fetch and decode data from network
// - Classification: EXACT — DataFetchService.fetch<[Product]> covers 100% of the need
// - Reuse misses: 1 → SEVERE
