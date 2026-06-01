"""
solid-description: Compliant user persistence and notification — single-responsibility types with protocol-injected dependencies and narrow role protocols.
solid-category: service
solid-tags: [user, persistence, notification, email]
"""

import Foundation

// ── Domain model ──────────────────────────────────────────────────────────────

struct User {
    let id: String
    let name: String
    let email: String

    var isValid: Bool { !name.isEmpty && hasValidEmail }
    var hasValidEmail: Bool { !email.isEmpty && email.contains("@") }
    var formattedEmail: String { "<\(email)>" }
}

// ── Role protocols ────────────────────────────────────────────────────────────

protocol UserStoring {
    func write(_ user: User)
    func read(_ id: String) -> User?
}

protocol EmailSending {
    func send(to address: String, body: String)
}

protocol ReportFormatting {
    func generate(from id: String) -> String
}

protocol Logging {
    func log(_ message: String)
}

// ── SRP: one cohesion group per type ─────────────────────────────────────────

// Persistence only — depends on injected UserStoring protocol
class UserRepository {
    private let store: UserStoring

    init(store: UserStoring) {
        self.store = store
    }

    func save(_ user: User) {
        guard user.isValid else { return }
        store.write(user)
    }

    func find(id: String) -> User? {
        return store.read(id)
    }
}

// Notification only — depends on injected EmailSending protocol
class UserNotifier {
    private let sender: EmailSending

    init(sender: EmailSending) {
        self.sender = sender
    }

    func sendWelcome(to user: User) {
        guard user.hasValidEmail else { return }
        sender.send(to: user.email, body: "Welcome, \(user.name)!")
    }
}

// Reporting only — depends on injected store + logger
class UserReportGenerator: ReportFormatting {
    private let store: UserStoring
    private let logger: Logging

    init(store: UserStoring, logger: Logging) {
        self.store = store
        self.logger = logger
    }

    func generate(from id: String) -> String {
        logger.log("Generating report for \(id)")
        guard let user = store.read(id) else { return "" }
        return "Report: \(user.name) <\(user.email)>"
    }
}

// ── ISP: narrow conformer protocols ──────────────────────────────────────────

// Persistence actions only — 2 methods, conformers implement 100%
protocol UserPersisting {
    func save(_ user: User)
    func find(id: String) -> User?
}

// Notification actions only — 1 method, conformers implement 100%
protocol UserNotifying {
    func sendWelcome(to user: User)
}

extension UserRepository: UserPersisting {}
extension UserNotifier: UserNotifying {}
