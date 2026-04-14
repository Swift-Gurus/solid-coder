

// Forced by System framework
final class NetworkSender {
    let session: URLSession
    func sendRequest(url: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(url)
        if let httpResponse = response as? HTTPURLResponse {
           //process error, status code etc

           return data
        }

        return data
    }
}

// Forced by System framework
final class MyDecoder {
    func decode(data: Data) -> [String: Any] {
     guard let dictionary = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
        return [:]
     }
     return dictionary
    }
}

final class MyObject {
   var particularValue: String
}

protocol MyCustomInterface {
   var requiredAttribute: String { get }
}

// wrong abstraction, not forced by any framework, but developer choice
final class MyWrongAbstractionUsage {

   func process(obj: MyCustomInterface) {
      guard let obj = obj as? MyObject else { return }
   }
}