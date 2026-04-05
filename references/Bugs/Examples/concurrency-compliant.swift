// BUG-3 COMPLIANT: Actor isolation, async dispatch, proper synchronization

import Foundation

// Safe: actor protects all shared mutable state
actor SessionManager {
    static let shared = SessionManager()
    private(set) var currentUser: User?
    private(set) var sessionToken: String?

    // Safe: @MainActor for UI updates, no sync dispatch
    @MainActor
    func updateUI(with user: User) {
        NotificationCenter.default.post(name: .userUpdated, object: nil)
    }

    // Safe: actor isolation protects sessionToken
    func refreshToken() async {
        let newToken = await fetchNewToken()
        sessionToken = newToken // actor-isolated, safe
    }

    func setCurrentUser(_ user: User) {
        currentUser = user
    }

    // Safe: async loading off main thread
    func loadUserProfile() async throws -> UserProfile {
        guard let url = URL(string: "https://api.example.com/me") else {
            throw SessionError.invalidURL
        }
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(UserProfile.self, from: data)
    }

    private func fetchNewToken() async -> String { "token" }
}

// Safe: actor protects shared download state
actor DownloadManager {
    private var activeDownloads: [URL: Progress] = [:]

    func startDownload(url: URL) {
        activeDownloads[url] = Progress(totalUnitCount: 100)
        Task {
            await performDownload(url: url)
        }
    }

    func cancelDownload(url: URL) {
        activeDownloads.removeValue(forKey: url)
    }

    func downloadCount() -> Int {
        return activeDownloads.count
    }

    // Safe: async/await instead of semaphore blocking
    func waitForDownload(url: URL) async -> Data? {
        return await fetchData(from: url)
    }

    private func performDownload(url: URL) async {}
    private func fetchData(from url: URL) async -> Data? { nil }
}

// Safe: actor-isolated global config instead of mutable global
actor AppConfig {
    static let shared = AppConfig()
    private var config: [String: Any] = [:]

    func get(_ key: String) -> Any? { config[key] }
    func set(_ key: String, value: Any) { config[key] = value }
}

enum SessionError: Error {
    case invalidURL
}

struct User: Codable {
    let id: String
    let name: String
}

struct UserProfile: Codable {
    let name: String
}

extension Notification.Name {
    static let userUpdated = Notification.Name("userUpdated")
}
