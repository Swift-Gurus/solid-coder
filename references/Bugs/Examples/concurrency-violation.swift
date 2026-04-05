// BUG-3 VIOLATION: Data races, deadlock risk, main-thread blocking, unsafe shared state

import Foundation

// BUG-3: static var on non-actor class — shared mutable state without synchronization
class SessionManager {
    static var shared = SessionManager()
    var currentUser: User? // mutable, accessed from any thread
    var sessionToken: String? // mutable, no synchronization

    // BUG-3: deadlock risk — DispatchQueue.main.sync potentially called from main
    func updateUI(with user: User) {
        DispatchQueue.main.sync { // deadlock if already on main thread
            self.currentUser = user
            NotificationCenter.default.post(name: .userUpdated, object: nil)
        }
    }

    // BUG-3: data race — mutating shared state from background without sync
    func refreshToken() {
        DispatchQueue.global().async {
            let newToken = self.fetchNewToken()
            self.sessionToken = newToken // race with main-thread reads
        }
    }

    // BUG-3: main-thread blocking — synchronous network I/O on main
    func loadUserProfile() -> UserProfile? {
        guard let url = URL(string: "https://api.example.com/me") else { return nil }
        let data = try? Data(contentsOf: url) // blocks main thread
        guard let data = data else { return nil }
        return try? JSONDecoder().decode(UserProfile.self, from: data)
    }

    private func fetchNewToken() -> String { "token" }
}

// BUG-3: data race — class with var properties accessed from closures without sync
class DownloadManager {
    var activeDownloads: [URL: Progress] = [:] // no synchronization
    private let queue = DispatchQueue(label: "downloads")

    func startDownload(url: URL) {
        // BUG-3: accessing activeDownloads from background queue without sync
        DispatchQueue.global().async {
            self.activeDownloads[url] = Progress(totalUnitCount: 100)
            self.performDownload(url: url)
        }
    }

    func cancelDownload(url: URL) {
        // Race: main thread accesses same dictionary
        activeDownloads.removeValue(forKey: url)
    }

    func downloadCount() -> Int {
        // Race: reads while background thread may be writing
        return activeDownloads.count
    }

    // BUG-3: semaphore.wait() risks blocking main thread
    func waitForDownload(url: URL) -> Data? {
        let semaphore = DispatchSemaphore(value: 0)
        var result: Data?

        DispatchQueue.global().async {
            result = self.fetchData(from: url)
            semaphore.signal()
        }

        semaphore.wait() // blocks calling thread — deadlock if main
        return result
    }

    private func performDownload(url: URL) {}
    private func fetchData(from url: URL) -> Data? { nil }
}

// BUG-3: global mutable variable
var globalConfig: [String: Any] = [:] // accessed from anywhere, no protection

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
