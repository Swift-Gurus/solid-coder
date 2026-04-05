// BUG-1 COMPLIANT: Safe unwrapping, guarded access, proper error handling

import Foundation

class UserProfileLoader {
    private let apiClient: APIClient
    private var cachedProfiles: [String: UserProfile] = [:]

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    // Safe: guard let + throws instead of force unwrap
    func loadProfile(for userID: String) throws -> UserProfile {
        guard let url = URL(string: "https://api.example.com/users/\(userID)") else {
            throw ProfileError.invalidURL(userID)
        }

        let data = try Data(contentsOf: url)
        let profile = try JSONDecoder().decode(UserProfile.self, from: data)
        return profile
    }

    // Safe: optional cast with guard
    func parseResponse(_ response: Any) throws -> [String: Any] {
        guard let dict = response as? [String: Any] else {
            throw ProfileError.invalidResponse
        }
        return dict
    }

    // Safe: bounds check before access
    func getProfileAt(index: Int) -> UserProfile? {
        let profiles = Array(cachedProfiles.values)
        guard profiles.indices.contains(index) else {
            return nil
        }
        return profiles[index]
    }

    // Safe: optional chaining with nil coalescing
    func getCachedName(for userID: String) -> String {
        return cachedProfiles[userID]?.name ?? "Unknown"
    }

    // Safe: .first returns optional, handled with if-let
    func getMostRecent() -> UserProfile? {
        let sorted = cachedProfiles.values.sorted { $0.lastActive > $1.lastActive }
        return sorted.first
    }

    // Safe: error is logged and handled, not silently discarded
    func preloadProfile(for userID: String) {
        do {
            let profile = try loadRemoteProfile(userID)
            cachedProfiles[userID] = profile
        } catch {
            logger.warning("Failed to preload profile for \(userID): \(error)")
        }
    }

    private func loadRemoteProfile(_ id: String) throws -> UserProfile {
        fatalError("Not implemented")
    }

    private let logger = Logger()
}

enum ProfileError: Error {
    case invalidURL(String)
    case invalidResponse
}

struct UserProfile: Codable {
    let name: String
    let email: String
    let lastActive: Date
}

protocol APIClient {}
struct Logger {
    func warning(_ message: String) {}
}
