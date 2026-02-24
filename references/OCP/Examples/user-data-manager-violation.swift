class UserDatabaseManager {

    func updateUserData() async throws {

        // Direct URL API, acceptable usage of the framework
        guard let url = URL(string: "https://endpointToUserData") else {
            throw UserError.malformedURL
        }

        // Sealed point 1: impossible to mock and test
        let (data, response) = try await URLSession().data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw UserError.requestFailed
        }

        // Sealed point 2: Possible to test, changing parsing from json to xml requires modification
        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let userJson = json?["user"] as? [String: Any] else {
            throw UserError.malformedData
        }

        // Sealed point 3: impossible to mock, impossible to swap storage
        let realm = try Realm()
        try realm.write {
            realm.add(User(jsonData: userJson))
        }
    }
}
