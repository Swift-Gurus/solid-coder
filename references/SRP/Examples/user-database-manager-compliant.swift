final class UserDataUpdater {
    private let fetcher: UserDataFetching
    private let parser: UserDataParsing
    private let repository: UserPersisting

    init(fetcher: UserDataFetching,
         parser: UserDataParsing,
         repository: UserPersisting) {
        self.fetcher = fetcher
        self.parser = parser
        self.repository = repository
    }

    func updateUserData() async throws {
        let data = try await fetcher.fetchUserData()
        let user = try parser.parseUser(from: data)
        try repository.save(user)
    }
}

final class RemoteUserDataFetcher: UserDataFetching {
    private let session: URLSessionProtocol
    private let url: URL

    init(session: URLSessionProtocol, url: URL) {
        self.session = session
        self.url = url
    }

    func fetchUserData() async throws -> Data {
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw UserDataError.requestFailed
        }

        return data
    }
}

final class JSONUserParser: UserDataParsing {
    func parseUser(from data: Data) throws -> User {
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]

        guard let userJson = json?["user"] as? [String: Any] else {
            throw UserDataError.malformedData
        }

        return User(jsonData: userJson)
    }
}

final class RealmUserRepository: UserPersisting {
    private let realmProvider: RealmProviding

    init(realmProvider: RealmProviding) {
        self.realmProvider = realmProvider
    }

    func save(_ user: User) throws {
        let realm = try realmProvider.realm()
        try realm.write {
            realm.add(user)
        }
    }
}

protocol URLSessionProtocol: Sendable {
    func data(from url: URL) async throws -> (Data, URLResponse)
}

extension URLSession: URLSessionProtocol {}

/// Abstracts Realm creation for testability (OCP compliant)
protocol RealmProviding: Sendable {
    func realm() throws -> Realm
}

final class DefaultRealmProvider: RealmProviding {
    func realm() throws -> Realm {
        try Realm()
    }
}

enum UserDataError: Error {
    case malformedURL
    case malformedData
    case requestFailed
}

class User: Object {
    convenience init(jsonData: [String: Any]) {
        self.init()
        // Parse JSON fields
    }
}
