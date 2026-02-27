

final class NetworkSender {
    let session: URLSession
    func sendRequest(url: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(url)
        if let httpResponse = response as? HTTPURLResponse {
           //process error, status code etc
        }
    }
}


final class MyDecoder {
    func decode(data: Data) -> [String: Any] {
       if let dictionary = try JSONSerialization.jsonObject(data) as? [String: Any] else {
          return [:]
       }
    }
}