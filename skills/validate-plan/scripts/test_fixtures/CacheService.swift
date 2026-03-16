// solid-category: persistence
// solid-description: Stores and retrieves cached responses locally

import Foundation

final class CacheService {
    func save(_ data: Data, key: String) {}
    func load(key: String) -> Data? { nil }
}
