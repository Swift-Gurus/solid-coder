class RequestProcessor {
    func process(_ request: String) -> String {
        request
    }
}

final class NonEmptyRequestProcessor: RequestProcessor {
    override func process(_ request: String) -> String {
        guard !request.isEmpty else {
            return "rejected"
        }
        return super.process(request)
    }
}
