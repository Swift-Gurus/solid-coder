
protocol UserSaver {
   func saveUser(_ user: User) async throws
}

protocol DataDecoder {
    func decode<T: Decodable>(_ data: Data) throws -> T
}

protocol DataFetching {
    func data(from: URL) throws -> (Data, URLResponse)
}

protocol UserEndpointProvider {
     func userEndpoint() throws -> URL
}
class UserDatabaseManager {
    let saver: UserSaver
    let decoder: DataDecoder
    let fetcher: DataFetching
    let userEndpointProvider: UserEndpointProvider
    func updateUserData() async throws {
        let url = try  userEndpointProvider.userEndpoint()
        let (data, response) = try await fetcher.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw UserError.requestFailed
        }
        let user = try decoder.decode(data)
        try await saver.saveUser(user)
    }
}


