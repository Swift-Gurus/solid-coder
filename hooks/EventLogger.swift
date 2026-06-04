/**
solid-description: Logs application events with an associated severity level.
solid-category: service
*/

protocol EventLogging {
    func log(_ event: String, level: LogLevel)
}

enum LogLevel {
    case info, warning, error
}

class EventLogger: EventLogging {
    private let output: TextOutputStream
    private let formatter: DateFormatter

    init(output: TextOutputStream, formatter: DateFormatter) {
        self.output = output
        self.formatter = formatter
    }

    func log(_ event: String, level: LogLevel) {
        let prefix = formatter.string(from: Date())
        var stream = output
        stream.write("[\(prefix)] [\(level)] \(event)")
    }
}

