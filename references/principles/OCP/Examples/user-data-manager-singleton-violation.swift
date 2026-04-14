class UserDatabaseManager {
    func updateUserData(completion: @escaping ((Error?) -> Void)) {

        NetworkManager.shared.fetchUserData { (user, error) in
            guard let user = user else {
                completion(error)
                return
            }
            DatabaseRealmAdapter.shared.saveUser(user) { completion($0) }
        }
    }
}

class NetworkManager {
    static let shared = NetworkManager()
    private init() {}
    func fetchUserData(completion: @escaping (User?, Error?) -> Void) { }
}

class DatabaseRealmAdapter {
    static let shared = DatabaseRealmAdapter()
    private init() {}
    func saveUser(_ user: User, completion: @escaping (Error?) -> Void) { }
}

struct User {}
