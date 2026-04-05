// BUG-1 VIOLATION: Multiple force unwraps, unguarded access, unhandled optionals

import Foundation

class UserProfileLoader {
    private let apiClient: APIClient
    private var cachedProfiles: [String: UserProfile] = [:]

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    // BUG-1: force unwrap — crashes if URL is invalid
    func loadProfile(for userID: String) -> UserProfile {
        let url = URL(string: "https://api.example.com/users/\(userID)")!

        // BUG-1: try! — crashes on network/decode error
        let data = try! Data(contentsOf: url)
        let profile = try! JSONDecoder().decode(UserProfile.self, from: data)

        return profile
    }

    // BUG-1: force cast — crashes on type mismatch
    func parseResponse(_ response: Any) -> [String: Any] {
        return response as! [String: Any]
    }

    // BUG-1: unguarded array access — crashes if index out of bounds
    func getProfileAt(index: Int) -> UserProfile {
        let profiles = Array(cachedProfiles.values)
        return profiles[index]
    }

    // BUG-1: force unwrap on dictionary lookup
    func getCachedName(for userID: String) -> String {
        return cachedProfiles[userID]!.name
    }

    // BUG-1: .first! — crashes on empty array
    func getMostRecent() -> UserProfile {
        let sorted = cachedProfiles.values.sorted { $0.lastActive > $1.lastActive }
        return sorted.first!
    }

    // BUG-1: try? discarding both error and value
    func preloadProfile(for userID: String) {
        _ = try? loadRemoteProfile(userID)
    }

    private func loadRemoteProfile(_ id: String) throws -> UserProfile {
        fatalError("Not implemented")
    }
}

struct UserProfile: Codable {
    let name: String
    let email: String
    let lastActive: Date
}

protocol APIClient {}
