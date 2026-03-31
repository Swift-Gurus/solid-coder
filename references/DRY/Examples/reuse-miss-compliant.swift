// DRY-1 Compliant: Reuse of existing type
// The existing DataFetchService is used instead of creating a duplicate.

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

// ✅ Compliant: ProductRepository uses the existing DataFetching protocol

final class ProductRepository {
    private let fetcher: DataFetching

    init(fetcher: DataFetching) {
        self.fetcher = fetcher
    }

    func loadProducts() async throws -> [Product] {
        try await fetcher.fetch(from: "/api/products")
    }
}

// Analysis:
// - ProductRepository delegates fetching to the existing DataFetching abstraction
// - No duplicate fetch/decode logic
// - Reuse misses: 0 → COMPLIANT
