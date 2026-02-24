import Foundation
import RealmSwift

class UserDatabaseManager {

    // Responsibility 1: URL Construction
    // Responsibility 2: Network Request Execution
    // Responsibility 3: Response Validation + Error Handling
    // Responsibility 4: JSON Parsing and Validation
    // Responsibility 5: Database Persistence
    func updateUserData() async throws {

        // Responsibility 1: URL Construction
        guard let url = URL(string: "https://endpointToUserData") else {
            throw UserError.malformedURL
        }

        // Responsibility 2: Network Request Execution
        let (data, response) = try await URLSession.shared.data(from: url)

        // Responsibility 3: Response Validation
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw UserError.requestFailed
        }

        // Responsibility 4: JSON Parsing and Validation
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let userJson = json?["user"] as? [String: Any] else {
            throw UserError.malformedData
        }

        // Responsibility 5: Database Persistence
        let realm = try Realm()
        try realm.write {
            realm.add(User(jsonData: userJson))
        }
    }
}

// Supporting types
enum UserError: Error {
    case malformedURL
    case malformedData
    case requestFailed
}

class User: Object {
    convenience init(jsonData: [String: Any]) {
        self.init()
        // Parse JSON
    }
}

