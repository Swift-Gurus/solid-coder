// solid-description: Test fixture with intentional SOLID violations for health-check testing.
// solid-category: test-fixture

import Foundation

// SRP violation: UserManager handles persistence, networking, formatting AND auth — 4 cohesion groups.

protocol UserPersisting {
    func saveUser(_ user: User)
    func loadUser(id: String) -> User?
}

protocol UserNetworking {
    func fetchRemoteProfile(id: String, completion: @escaping (Data?) -> Void)
    func uploadAvatar(_ data: Data, userId: String)
}

protocol UserFormatting {
    func formatDisplayName(_ user: User) -> String
    func formatJoinDate(_ user: User) -> String
}

protocol UserAuthenticating {
    func login(email: String, password: String) -> Bool
    func logout(userId: String)
}

class UserPersistenceService: UserPersisting {
    private let db: SQLiteDatabase
    private let logger: Logger
    init(db: SQLiteDatabase = SQLiteDatabase(), logger: Logger = .shared) {
        self.db = db
        self.logger = logger
    }
    func saveUser(_ user: User) {
        db.execute("INSERT INTO users VALUES (?)", user.id)
        logger.log("saved \(user.id)")
    }
    func loadUser(id: String) -> User? {
        db.query("SELECT * FROM users WHERE id = ?", id)
        return nil
    }
}

class UserNetworkService: UserNetworking {
    private let network: URLSession
    init(network: URLSession = .shared) { self.network = network }
    func fetchRemoteProfile(id: String, completion: @escaping (Data?) -> Void) {
        let url = URL(string: "https://api.example.com/users/\(id)")!
        network.dataTask(with: url) { data, _, _ in completion(data) }.resume()
    }
    func uploadAvatar(_ data: Data, userId: String) {
        var request = URLRequest(url: URL(string: "https://api.example.com/avatars")!)
        request.httpMethod = "POST"
        network.uploadTask(with: request, from: data) { _, _, _ in }.resume()
    }
}

class UserFormattingService: UserFormatting {
    func formatDisplayName(_ user: User) -> String {
        "\(user.firstName) \(user.lastName)".trimmingCharacters(in: .whitespaces)
    }
    func formatJoinDate(_ user: User) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter.string(from: user.joinDate)
    }
}

class UserAuthService: UserAuthenticating {
    private let db: SQLiteDatabase
    init(db: SQLiteDatabase = SQLiteDatabase()) { self.db = db }
    func login(email: String, password: String) -> Bool {
        let hash = password.data(using: .utf8)!.base64EncodedString()
        return db.query("SELECT id FROM users WHERE email=? AND hash=?", email, hash) != nil
    }
    func logout(userId: String) {
        db.execute("DELETE FROM sessions WHERE user_id=?", userId)
    }
}

class UserManager {
    private let persistence: UserPersisting
    private let networking: UserNetworking
    private let formatting: UserFormatting
    private let auth: UserAuthenticating

    init(
        persistence: UserPersisting = UserPersistenceService(),
        networking: UserNetworking = UserNetworkService(),
        formatting: UserFormatting = UserFormattingService(),
        auth: UserAuthenticating = UserAuthService()
    ) {
        self.persistence = persistence
        self.networking = networking
        self.formatting = formatting
        self.auth = auth
    }

    func saveUser(_ user: User) { persistence.saveUser(user) }
    func loadUser(id: String) -> User? { persistence.loadUser(id: id) }
    func fetchRemoteProfile(id: String, completion: @escaping (Data?) -> Void) {
        networking.fetchRemoteProfile(id: id, completion: completion)
    }
    func uploadAvatar(_ data: Data, userId: String) {
        networking.uploadAvatar(data, userId: userId)
    }
    func formatDisplayName(_ user: User) -> String { formatting.formatDisplayName(user) }
    func formatJoinDate(_ user: User) -> String { formatting.formatJoinDate(user) }
    func login(email: String, password: String) -> Bool { auth.login(email: email, password: password) }
    func logout(userId: String) { auth.logout(userId: userId) }
}

// ISP-compliant: fat DataHandling split into four narrow role protocols.

protocol DataReading {
    func fetchData() -> Data
}

protocol DataWriting {
    func saveData(_ data: Data)
    func deleteData(id: String)
}

protocol DataPorting {
    func exportToCSV() -> String
    func importFromCSV(_ csv: String)
}

protocol DataTransforming {
    func encryptData(_ data: Data) -> Data
    func decryptData(_ data: Data) -> Data
    func compressData(_ data: Data) -> Data
    func decompressData(_ data: Data) -> Data
}

protocol DataHandling: DataReading, DataWriting, DataPorting, DataTransforming {}

// LSP-compliant: ReadOnlyDataStore only conforms to DataReading — no fatalError, no forced stubs.
class ReadOnlyDataStore: DataReading {
    func fetchData() -> Data { Data() }
}

// LSP-compliant: no type-switching — processStore depends on the narrowest protocol it needs.
func processStore(_ store: DataReading) {
    let data = store.fetchData()
    print("processing \(data.count) bytes")
}

class WritableDataStore: DataHandling {
    func fetchData() -> Data { Data() }
    func saveData(_ data: Data) { /* write data */ }
    func deleteData(id: String) { /* delete by id */ }
    func exportToCSV() -> String { "" }
    func importFromCSV(_ csv: String) { /* import csv */ }
    func encryptData(_ data: Data) -> Data { data }
    func decryptData(_ data: Data) -> Data { data }
    func compressData(_ data: Data) -> Data { data }
    func decompressData(_ data: Data) -> Data { data }
}

// Stub types to make the file compile-coherent.
struct User { var id: String; var firstName: String; var lastName: String; var joinDate: Date }
class SQLiteDatabase {
    @discardableResult func execute(_ sql: String, _ args: Any...) -> Bool { false }
    func query(_ sql: String, _ args: Any...) -> Any? { nil }
}
class Logger { static let shared = Logger(); func log(_ msg: String) {} }
