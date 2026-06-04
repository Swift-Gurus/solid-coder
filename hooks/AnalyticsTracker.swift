/**
solid-description: Records and dispatches application analytics events — such as purchases, page views, and errors — for delivery to a backend collection service.
solid-category: service
*/

protocol EventTransport {
    func send(endpoint: String, data: [String: Any])
}

class AnalyticsTracker {
    private let transport: EventTransport

    init(transport: EventTransport) {
        self.transport = transport
    }

    func trackPurchase(orderId: String, amount: Double) {
        transport.send(endpoint: "purchase", data: ["orderId": orderId, "amount": amount])
    }

    func trackPageView(screen: String) {
        transport.send(endpoint: "pageview", data: ["screen": screen])
    }

    func trackError(code: Int, message: String) {
        transport.send(endpoint: "error", data: ["code": code, "message": message])
    }
}

class HTTPEventTransport: EventTransport {
    private let baseURL: URL
    private let session: URLSession

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    func send(endpoint: String, data: [String: Any]) {
        let url = baseURL.appendingPathComponent(endpoint)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.httpBody = try? JSONSerialization.data(withJSONObject: data)
        session.dataTask(with: request).resume()
    }
}
