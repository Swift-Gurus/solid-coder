import Foundation

protocol ReportSource {
    func report() -> String
}

struct DetailedReportSource: ReportSource {
    func report() -> String { "report" }
    func detailedReport() -> String { "details unavailable through ReportSource" }
}

struct InspectionConsumer {
    func render(_ source: any ReportSource) -> String {
        if let detailed = source as? DetailedReportSource {
            return detailed.detailedReport()
        }
        return source.report()
    }

    func loadStatus(_ request: URLRequest) async throws -> Int {
        let (_, response) = try await URLSession.shared.data(for: request)
        return statusCode(response)
    }

    func statusCode(_ response: URLResponse) -> Int {
        guard let http = response as? HTTPURLResponse else { return 0 }
        return http.statusCode
    }

    func logSourceType(_ source: any ReportSource) {
        print(type(of: source))
    }

    func inspectInferred(_ source: any ReportSource) -> Bool {
        let inferred = source
        return inferred is DetailedReportSource
    }
}
